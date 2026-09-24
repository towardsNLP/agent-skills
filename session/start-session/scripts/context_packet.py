#!/usr/bin/env python3
"""Build a bounded, read-only session card from project metadata.

This helper is the context boundary for ``start-session``. It reads the contributor
profile, the contributor's current state, the selected ticket, and diary headings
inside the process so those documents do not have to enter an LLM's context. Only
the card written to stdout is intended for the conversation.

The output budget is semantic rather than a character slicer: field values are
always emitted whole. If complete task-routing fields do not fit, the helper emits
a small blocked card with source pointers instead of clipping a goal, governing
anchor, or acceptance command into something that could change its meaning.

The script is intentionally read-only and uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_DEFAULT = Path("planning/agent/profile.md")
DEFAULT_MAX_CHARS = 2500
# Below this the fixed blocked-card message alone does not fit, so the budget
# could not be honoured even by returning nothing useful. Refuse instead.
MIN_MAX_CHARS = 800
LONG_FIELD_CHARS = 240

_PROFILE_FIELD = re.compile(r"^\s*-\s+\*\*([A-Za-z_][A-Za-z0-9_]*):\*\*\s*(.*)$")
_BOLD_FIELD = re.compile(r"^\s*-?\s*\*\*([^*]+):\*\*\s*(.*)$")
_DATE_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")
_NONE = {"", "-", "—", "none", "n/a", "not selected", "unclaimed"}


def one_line(value: str) -> str:
    """Normalize Markdown field text without changing its words or punctuation."""
    return " ".join(value.replace("`", "").split())


def path_value(value: str) -> str:
    """Strip commentary from a profile path while retaining ordinary hyphens."""
    value = value.strip()
    for separator in (" — ", " -- "):
        if separator in value:
            value = value.split(separator, 1)[0]
    return value.strip().strip("`").rstrip(".")


def contained(root: Path, path: Path) -> bool:
    """Check that a path stays inside the project once symlinks are followed."""
    try:
        return path.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def read_text(path: Path) -> str:
    """Return UTF-8 text, treating a missing or unreadable optional file as empty."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeError):
        return ""


def profile_fields(text: str) -> dict[str, str]:
    """Extract the first value for each ``- **key:** value`` profile field."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = _PROFILE_FIELD.match(line)
        if match:
            fields.setdefault(match.group(1), one_line(match.group(2)))
    return fields


def section_fields(text: str, section: str | None = None) -> dict[str, str]:
    """Read bold fields, including wrapped continuation lines."""
    fields: dict[str, str] = {}
    current_section = ""
    current_key: str | None = None

    for line in text.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip().casefold()
            current_key = None
            continue
        if section is not None and current_section != section.casefold():
            continue

        if not line.strip():
            current_key = None
            continue

        match = _BOLD_FIELD.match(line)
        if match:
            current_key = match.group(1).strip().casefold().replace(" ", "_")
            fields[current_key] = one_line(match.group(2))
            continue

        if current_key and not line.lstrip().startswith(("#", "- ")):
            fields[current_key] = one_line(f"{fields[current_key]} {line.strip()}")

    return fields


def git_value(root: Path, *args: str) -> str:
    """Run a bounded, read-only git query and return an empty string on failure."""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def contributor_slug(name: str) -> str:
    """Derive the filename slug used by the contributor state convention."""
    first = name.split()[0] if name.split() else ""
    return re.sub(r"[^a-z0-9]+", "", first.casefold())


def roster_contains(profile_text: str, contributor: str) -> bool | None:
    """Check the contributor roster, or return ``None`` when no roster is declared."""
    if not contributor:
        return None
    match = re.search(
        r"^## Identity and people\s*$([\s\S]*?)(?=^## |\Z)",
        profile_text,
        re.MULTILINE,
    )
    if not match or "contributors" not in match.group(1).casefold():
        return None
    # Whole name only. A substring test makes "Al" a member of a roster listing Alice.
    bounded = rf"(?<![\w-]){re.escape(contributor)}(?![\w-])"
    return re.search(bounded, match.group(1), re.IGNORECASE) is not None


def resolve_state(root: Path, profile: dict[str, str], contributor: str) -> Path | None:
    """Resolve one contributor state file without opening every candidate."""
    state_dir_value = path_value(profile.get("state_dir", "planning/agent/state/"))
    state_dir = root / state_dir_value
    slug = contributor_slug(contributor)

    if slug and (state_dir / f"{slug}.md").is_file():
        return state_dir / f"{slug}.md"

    candidates = sorted(path for path in state_dir.glob("*.md") if not path.name.startswith("."))
    if slug:
        matching = [path for path in candidates if slug in path.stem.casefold()]
        if len(matching) == 1:
            return matching[0]
    return candidates[0] if len(candidates) == 1 else None


def resolve_diary(root: Path, profile: dict[str, str], contributor: str) -> Path | None:
    """Resolve the contributor diary used only for the freshness comparison."""
    diary_dir = root / path_value(profile.get("diary_dir", "planning/diaries/"))
    slug = contributor_slug(contributor)
    pattern = path_value(profile.get("diary_filename", "<first>-diary.md"))
    candidate = diary_dir / pattern.replace("<first>", slug).replace("<name>", slug)
    if candidate.is_file():
        return candidate

    candidates = sorted(diary_dir.glob(f"*{slug}*.md")) if slug else []
    return candidates[0] if len(candidates) == 1 else None


def latest_date(path: Path | None) -> str:
    """Return the newest ISO date heading in a diary without importing its prose."""
    if path is None:
        return ""
    dates = [
        match.group(1)
        for line in read_text(path).splitlines()
        if (match := _DATE_HEADING.match(line))
    ]
    return max(dates, default="")


def ticket_root(profile: dict[str, str]) -> str:
    """Return the stable directory prefix before a ticket-path placeholder."""
    pattern = path_value(profile.get("ticket_dir", "planning/tickets/<spec-id>/"))
    marker_positions = [
        position for marker in ("<", "{") if (position := pattern.find(marker)) >= 0
    ]
    if not marker_positions:
        return pattern.rstrip("/")
    head = pattern[: min(marker_positions)]
    return head[: head.rfind("/")].rstrip("/") if "/" in head else head.rstrip("/")


def resolve_ticket(root: Path, profile: dict[str, str], task: str) -> Path | None:
    """Resolve an exact path or an unambiguous ``<spec-id>/<number>`` shorthand.

    A task that names a file outside the project resolves to ``None``. Reading it
    would widen the boundary this helper exists to hold, and an escaping path has no
    project-relative rendering for the card.
    """
    task = path_value(task)
    if task.casefold() in _NONE:
        return None

    direct = root / task
    if direct.is_file():
        return direct.resolve() if contained(root, direct) else None

    match = re.fullmatch(r"([^/]+)/([0-9]+)", task)
    if not match:
        return None
    spec_prefix, number = match.groups()
    base = root / ticket_root(profile)
    hits: list[Path] = []
    # Shorthand lookup is deliberately narrow: one matching ticket is required.
    for spec_dir in base.glob(f"{spec_prefix}*"):
        hits.extend(spec_dir.glob(f"{number.zfill(2)}-*.md"))
    if len(hits) != 1:
        return None
    # `ticket_dir` comes from the profile and may itself point outside the project.
    return hits[0].resolve() if contained(root, hits[0]) else None


def extract_branch(value: str) -> str:
    """Extract a branch name from either a Markdown code span or plain text."""
    match = re.search(r"`([^`]+)`", value)
    if match:
        return match.group(1)
    return value.split()[0] if value.split() else ""


def same_person(claimed_by: str, contributor: str) -> bool:
    """Compare a claim against full-name, first-name, and state-file conventions."""
    claim = one_line(claimed_by).casefold()
    person = one_line(contributor).casefold()
    if claim in _NONE:
        return True
    first = person.split()[0] if person.split() else ""
    return claim in {person, first, contributor_slug(contributor)}


@dataclass
class SessionCard:
    """Collect complete semantic fields and render them under a hard budget."""

    entries: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sources: list[Path] = field(default_factory=list)

    def add(self, label: str, value: str, source: Path | None = None) -> None:
        """Add one complete field; warn about poor source modeling without clipping it."""
        value = one_line(value)
        if value.casefold() in _NONE:
            return
        if len(value) > LONG_FIELD_CHARS:
            where = source.name if source else "its source"
            self.warnings.append(
                f"{label} is long in {where}; shorten the source field if the card exceeds budget."
            )
        # Never slice a semantic value. A clipped command or qualifier can reverse meaning.
        self.entries.append((label, value))

    def _shown_sources(self, root: Path) -> list[str]:
        """Render unique source paths relative to the project whenever possible."""
        shown_sources: list[str] = []
        for source in dict.fromkeys(self.sources):
            try:
                shown = source.relative_to(root)
            except ValueError:
                shown = source
            shown_sources.append(str(shown))
        return shown_sources

    @staticmethod
    def _output(lines: list[str]) -> str:
        """Join card lines using the exact representation used for budget checks."""
        return "\n".join(lines).strip() + "\n"

    def _fit(self, lines: list[str], heading: str, items: list[str], max_chars: int) -> list[str]:
        """Append whichever complete items fit, adding the heading only if one does."""
        heading_added = False
        for item in items:
            candidate = [*(lines if heading_added else [*lines, "", heading]), item]
            if len(self._output(candidate)) <= max_chars:
                lines = candidate
                heading_added = True
        return lines

    def _blocked_output(self, root: Path, max_chars: int) -> str:
        """Fail closed without returning a plausible but semantically partial task."""
        lines = [
            "# Session card",
            (
                "- **Status:** blocked — complete routing fields exceed "
                f"the {max_chars}-character budget"
            ),
            "- **Reason:** no field was clipped; a partial goal, constraint, or check is unsafe",
            (
                "- **Next:** shorten the source routing fields or name a narrower task; "
                "do not load broad documents"
            ),
        ]

        # Complete identity fields are useful for repair, but none is allowed to crowd
        # the fixed safety message or be cut merely to satisfy the ceiling.
        repair_labels = {"Ticket", "Work", "Work kind"}
        for label, value in self.entries:
            if label not in repair_labels:
                continue
            candidate = [*lines, f"- **{label}:** {value}"]
            if len(self._output(candidate)) <= max_chars:
                lines = candidate

        # A blocked card is the one that most needs these: a foreign claim or a trunk
        # branch is what should stop the session, and dropping them first would leave
        # the conflict invisible exactly when the card cannot show the work.
        lines = self._fit(
            lines, "## Warnings", [f"- {one_line(w)}" for w in self.warnings], max_chars
        )
        return self._output(
            self._fit(
                lines, "## Sources", [f"- `{s}`" for s in self._shown_sources(root)], max_chars
            )
        )

    def render(self, root: Path, max_chars: int) -> str:
        """Render the full card, or an explicitly blocked atomic-field fallback."""
        lines = ["# Session card"]
        lines.extend(f"- **{label}:** {value}" for label, value in self.entries)
        if self.warnings:
            lines.extend(["", "## Warnings"])
            lines.extend(f"- {one_line(warning)}" for warning in self.warnings)
        if self.sources:
            lines.extend(["", "## Sources"])
            lines.extend(f"- `{source}`" for source in self._shown_sources(root))

        output = self._output(lines)
        if len(output) <= max_chars:
            return output

        # Do not solve overflow with ``output[:max_chars]``: that can turn a safe
        # acceptance command or negated constraint into a different instruction.
        return self._blocked_output(root, max_chars)


def build_packet(
    root: Path,
    *,
    task: str = "",
    contributor: str = "",
    branch: str = "",
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Resolve project routing metadata and return one bounded session card."""
    if max_chars < MIN_MAX_CHARS:
        raise ValueError(f"max_chars must be at least {MIN_MAX_CHARS}")
    root = root.resolve()
    profile_path = root / PROFILE_DEFAULT
    profile_text = read_text(profile_path)
    profile = profile_fields(profile_text)
    contributor = contributor or git_value(root, "config", "user.name")
    branch = branch or git_value(root, "branch", "--show-current")

    card = SessionCard()
    if profile_text:
        card.sources.append(profile_path)
    else:
        card.warnings.append(f"Missing {PROFILE_DEFAULT}; project-specific routing is unavailable.")

    # Only the ``Now`` section becomes candidate output; historical state is ignored.
    state_path = resolve_state(root, profile, contributor)
    state_text = read_text(state_path) if state_path else ""
    state = section_fields(state_text, "Now")
    state_as_of_match = re.search(r"^\*\*state_as_of:\*\*\s*(\d{4}-\d{2}-\d{2})", state_text, re.M)
    state_as_of = state_as_of_match.group(1) if state_as_of_match else ""
    if state_path:
        card.sources.append(state_path)
    else:
        card.warnings.append("Contributor state is missing or ambiguous; name the task explicitly.")

    card.add("Contributor", contributor or "unknown")
    card.add("Branch", branch or "no git branch")
    card.add("Work", state.get("phase_/_workstream", ""), state_path)
    card.add("Work kind", state.get("work_kind", ""), state_path)

    state_ticket = state.get("ticket", "")
    ticket_path = resolve_ticket(root, profile, task or state_ticket)
    ticket_text = read_text(ticket_path) if ticket_path else ""
    ticket = section_fields(ticket_text)
    if ticket_path:
        card.sources.append(ticket_path)
        card.add("Ticket", str(ticket_path.relative_to(root)))
        card.add("Goal", ticket.get("what_becomes_true", ""), ticket_path)
        blocked_by = ticket.get("blocked_by", "")
        if blocked_by.casefold() not in _NONE:
            card.add("Declared dependency", f"{blocked_by} (not evaluated at startup)", ticket_path)
        card.add("Governs", ticket.get("governs", ""), ticket_path)
        check_type = ticket.get("check_type", "")
        check = ticket.get("check", "")
        card.add(
            "Acceptance", " — ".join(part for part in (check_type, check) if part), ticket_path
        )
        claimed_by = ticket.get("claimed_by", "")
        card.add(
            "Claim",
            "unclaimed (available)" if claimed_by.casefold() in _NONE else claimed_by,
            ticket_path,
        )
        if claimed_by and not same_person(claimed_by, contributor):
            card.warnings.append(
                f"Ticket is claimed by {one_line(claimed_by)}, not {contributor or 'this user'}."
            )
    elif task or state_ticket:
        card.warnings.append(
            f"No ticket inside the project resolves from {one_line(task or state_ticket)!r}."
        )
    else:
        card.add("Governing agreement", state.get("governing_spec", ""), state_path)
        card.add("Context anchors", state.get("context_anchors", ""), state_path)

    card.add("Question", state.get("question", ""), state_path)
    card.add("Evidence", state.get("evidence_context", ""), state_path)
    card.add("Last verified", state.get("last_verified", ""), state_path)
    card.add(
        "Next", state.get("next_action", "name the task before loading more context"), state_path
    )

    # The diary is reduced to date headings inside this process. Its entries never
    # become part of the generated card.
    diary_path = resolve_diary(root, profile, contributor)
    diary_date = latest_date(diary_path)
    if not state_as_of:
        card.warnings.append("State has no state_as_of date; freshness is unknown.")
    elif not diary_date:
        # Saying "current" here would report a comparison that never happened.
        card.warnings.append(f"No diary entry to compare against; state_as_of={state_as_of}.")
    elif diary_date > state_as_of:
        card.warnings.append(
            f"State is stale: state_as_of={state_as_of}, newest diary entry={diary_date}."
        )
    else:
        card.add("State freshness", f"current as of {state_as_of}")

    roster_match = roster_contains(profile_text, contributor)
    if roster_match is False:
        card.warnings.append(f"{contributor} is not present in the profile contributor roster.")

    recorded_branch = extract_branch(state.get("branch", ""))
    if branch and recorded_branch and branch != recorded_branch:
        card.warnings.append(
            f"Current branch {branch!r} differs from recorded branch {recorded_branch!r}."
        )
    if branch in {"main", "master", "trunk"}:
        rule = profile.get("branch_convention", "the project's topic-branch convention")
        card.warnings.append(
            f"{branch} is a trunk branch; create a topic branch before writes ({rule})."
        )

    return card.render(root, max_chars)


def parser() -> argparse.ArgumentParser:
    """Construct the command-line interface for direct and worker execution."""
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", type=Path, default=Path.cwd())
    result.add_argument("--task", default="", help="ticket path or <spec-id>/<ticket-number>")
    result.add_argument("--contributor", default="", help="override git config user.name")
    result.add_argument("--branch", default="", help="override git branch --show-current")
    result.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    return result


def main() -> int:
    """Validate CLI-only limits, print the packet, and return a shell status."""
    args = parser().parse_args()
    if args.max_chars < MIN_MAX_CHARS:
        print(f"--max-chars must be at least {MIN_MAX_CHARS}", file=sys.stderr)
        return 2
    print(
        build_packet(
            args.project_root,
            task=args.task,
            contributor=args.contributor,
            branch=args.branch,
            max_chars=args.max_chars,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
