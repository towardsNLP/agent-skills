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
        # S607: `git` is resolved from PATH on purpose. This script runs in whatever
        # workspace a host repo checks it out into, so an absolute path is not portable.
        result = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
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


def roster_names(profile_text: str) -> list[str]:
    """Full contributor names from the profile roster, or ``[]`` when none is declared."""
    match = re.search(
        r"^## Identity and people\s*$([\s\S]*?)(?=^## |\Z)", profile_text, re.MULTILINE
    )
    if not match:
        return []
    section = match.group(1)
    start = section.casefold().find("**contributors:**")
    if start < 0:
        return []
    names: list[str] = []
    for line in section[start:].splitlines()[1:]:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            break  # dedented back to another profile key
        entry = line.strip()
        if not entry.startswith("- "):
            continue
        # "Dana Okafor — platform, handing off" -> "Dana Okafor". An em dash separates
        # the name from the role; a plain hyphen does not, because names contain them.
        names.append(entry[2:].split("—")[0].strip())
    return [name for name in names if name]


def full_name_slug(name: str) -> str:
    """The surname-disambiguated slug the profile convention declares.

    ``Dana Okafor`` -> ``dana-okafor``; ``Maria Del Rio`` -> ``maria-delrio``.
    First name, hyphen, then the remaining parts run together — which is the form the
    profile already gives as its own example, so the script matches the declared
    convention rather than inventing a second one.
    """
    parts = [re.sub(r"[^a-z0-9]+", "", part.casefold()) for part in name.split()]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        return ""
    return f"{parts[0]}-{''.join(parts[1:])}"


def ambiguous_first_names(profile_text: str) -> set[str]:
    """Slugs that more than one roster name reduces to.

    **The convention is first-name-based and the roster is not.** `state_dir/<first>.md`
    and `<first>-diary.md` both key on the first name, so two contributors sharing one --
    `Dana Okafor` and `Dana Whitfield`, say -- resolve to the same files. The
    resolvers below refuse rather than guess, because the failure is silent otherwise: the
    card loads, names the right contributor, and carries someone else's state and work.
    That also breaks the one-writer rule the state convention rests on.
    """
    counts: dict[str, int] = {}
    for name in roster_names(profile_text):
        slug = contributor_slug(name)
        if slug:
            counts[slug] = counts.get(slug, 0) + 1
    return {slug for slug, count in counts.items() if count > 1}


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


def resolve_state(
    root: Path,
    profile: dict[str, str],
    contributor: str,
    ambiguous: set[str] | None = None,
) -> Path | None:
    """Resolve one contributor state file without opening every candidate.

    Returns ``None`` when the first name is shared on the roster: a wrong state file is
    worse than none, because nothing downstream can tell it apart from the right one.
    """
    state_dir_value = path_value(profile.get("state_dir", "planning/agent/state/"))
    state_dir = root / state_dir_value
    slug = contributor_slug(contributor)

    # The profile declares the rule -- "collisions disambiguated by surname" -- so try the
    # surname-disambiguated name first, whether or not this first name collides. A project
    # that has never had a collision is unaffected; one that has gets the right file.
    full = full_name_slug(contributor)
    if full and full != slug and (state_dir / f"{full}.md").is_file():
        return state_dir / f"{full}.md"
    if slug and slug in (ambiguous or set()):
        return None

    if slug and (state_dir / f"{slug}.md").is_file():
        return state_dir / f"{slug}.md"

    # **NO SINGLETON FALLBACK** [2026-09-25]. This used to end
    # `return candidates[0] if len(candidates) == 1 else None`, so in a repository with one
    # state file *every* contributor resolved to it. Reproduced on a live roster: two
    # contributors with no state file of their own each received a third's branch,
    # evidence and next action, on a card headed with their own name. A convenience for
    # the first contributor turns into silent misattribution for the second, and the state
    # convention's one-writer rule cannot survive it.
    #
    # The substring match below stays: it is bounded by the slug, so `dana` finds
    # `dana-okafor.md` but `maria` finds nothing. An empty result is the right answer --
    # a missing state file is normal before a contributor's first `/end-session`, and the
    # card says so.
    if not slug:
        return None
    matching = [path for path in sorted(state_dir.glob("*.md"))
                if not path.name.startswith(".") and path.stem.casefold().startswith(slug)]
    return matching[0] if len(matching) == 1 else None


def resolve_diary(
    root: Path,
    profile: dict[str, str],
    contributor: str,
    ambiguous: set[str] | None = None,
) -> Path | None:
    """Resolve the contributor diary used only for the freshness comparison."""
    diary_dir = root / path_value(profile.get("diary_dir", "planning/diaries/"))
    slug = contributor_slug(contributor)
    pattern = path_value(profile.get("diary_filename", "<first>-diary.md"))

    full = full_name_slug(contributor)
    if full and full != slug:
        disambiguated = diary_dir / pattern.replace("<first>", full).replace("<name>", full)
        if disambiguated.is_file():
            return disambiguated
    if slug and slug in (ambiguous or set()):
        return None

    candidate = diary_dir / pattern.replace("<first>", slug).replace("<name>", slug)
    if candidate.is_file():
        return candidate

    # Anchored, not `*{slug}*`: a substring glob matches a name that merely contains the
    # slug. Same class as the singleton fallback removed from `resolve_state` above, and
    # cheaper to fix than to reason about each time the roster changes.
    candidates = sorted(p for p in diary_dir.glob("*.md")
                        if p.stem.casefold().startswith(slug)) if slug else []
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

    ambiguous = ambiguous_first_names(profile_text)
    shared_first_name = contributor_slug(contributor) in ambiguous

    # Only the ``Now`` section becomes candidate output; historical state is ignored.
    state_path = resolve_state(root, profile, contributor, ambiguous)
    state_text = read_text(state_path) if state_path else ""
    state = section_fields(state_text, "Now")
    state_as_of_match = re.search(r"^\*\*state_as_of:\*\*\s*(\d{4}-\d{2}-\d{2})", state_text, re.M)
    state_as_of = state_as_of_match.group(1) if state_as_of_match else ""
    if state_path:
        card.sources.append(state_path)
    elif shared_first_name:
        sharing = [n for n in roster_names(profile_text)
                   if contributor_slug(n) == contributor_slug(contributor)]
        card.warnings.append(
            f"{contributor or 'This user'} shares a first name with "
            f"{', '.join(n for n in sharing if n != contributor) or 'another contributor'} "
            f"on the roster, and state and diary files key on the first name. Refusing to "
            f"guess which is yours -- name the task explicitly."
        )
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
    elif (named := (task or state_ticket)) and named.casefold() not in _NONE:
        # A none-word is a filled field saying there is no ticket, which is the normal state
        # of a repo before the first one is cut -- and `templates/state.md` tells the writer to
        # put "none" there. `resolve_ticket` already treats it as absent; warning on it made a
        # correctly-written state file report a defect on every session card.
        card.warnings.append(f"No ticket inside the project resolves from {one_line(named)!r}.")
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
    diary_path = resolve_diary(root, profile, contributor, ambiguous)
    diary_date = latest_date(diary_path)
    # **The diary is not the only thing that moves.** Comparing state only against diary
    # headings reported "current" across seven commits that reversed a decision the state
    # file still described, because no diary entry had been written in between. Committed
    # work is the other clock, and it is the one that makes state wrong.
    # **Revision identity, not a calendar date** [2026-09-25]. This was `--format=%cs`, which
    # reduces freshness to `YYYY-MM-DD`: state committed at 20:11 and a HEAD three commits
    # later at 20:27 compared equal, so a card presented "no SOURCE.lock" and "20 commits"
    # as current on a tree that had both. Most stale state is same-day -- that is what a
    # working session looks like -- so a day-resolution clock misses the common case and
    # catches only the one somebody would already have noticed.
    #
    # Asking whether HEAD has moved past the state file's own last commit answers it at
    # any resolution. Empty outside git, or before the file is committed; both fall
    # through to the diary comparison rather than claiming freshness.
    state_rev = (git_value(root, "log", "-1", "--format=%H", "--", str(state_path))
                 if state_path else "")
    head_rev = git_value(root, "rev-parse", "HEAD")
    commits_since = ""
    if state_rev and head_rev and state_rev != head_rev:
        commits_since = git_value(root, "rev-list", "--count", f"{state_rev}..{head_rev}")
    if not state_as_of:
        card.warnings.append("State has no state_as_of date; freshness is unknown.")
    elif diary_date and diary_date > state_as_of:
        card.warnings.append(
            f"State is stale: state_as_of={state_as_of}, newest diary entry={diary_date}."
        )
    elif commits_since and commits_since != "0":
        card.warnings.append(
            f"State predates the work: {commits_since} commit(s) have landed since "
            f"{state_rev[:8]}, which last wrote it. state_as_of={state_as_of}."
        )
    elif not diary_date:
        # Saying "current" here would report a comparison that never happened.
        card.warnings.append(f"No diary entry to compare against; state_as_of={state_as_of}.")
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
