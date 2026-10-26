#!/usr/bin/env python3
"""Build a bounded, read-only session card from project metadata.

This helper is the context boundary for ``start-session``. It reads the contributor
profile, the contributor's current state, the selected ticket, diary headings and the
roadmap's current week inside the process so those documents do not have to enter an
LLM's context. Only the card written to stdout is intended for the conversation.

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
from datetime import date, timedelta
from pathlib import Path

PROFILE_DEFAULT = Path("planning/agent/profile.md")
DEFAULT_MAX_CHARS = 2500
# The week block has its own ceiling, so a heavy week can never block the routing card.
WEEK_MAX_CHARS = 1500
MILESTONES_AHEAD = 3
# Below this the fixed blocked-card message alone does not fit, so the budget
# could not be honoured even by returning nothing useful. Refuse instead.
MIN_MAX_CHARS = 800
LONG_FIELD_CHARS = 240

_PROFILE_FIELD = re.compile(r"^\s*-\s+\*\*([A-Za-z_][A-Za-z0-9_]*):\*\*\s*(.*)$")
_BOLD_FIELD = re.compile(r"^\s*-?\s*\*\*([^*]+):\*\*\s*(.*)$")
_DATE_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\b")
_NONE = {"", "-", "—", "none", "n/a", "not selected", "unclaimed"}

_MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
_MONTH_DAY = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(\d{1,2})\b"
)
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_WEEK_TITLE = re.compile(r"^Weeks?\s+\d.*\(([^()]*)\)$")
_ITEM = re.compile(r"^-\s+(?:\[([ xX])\]\s+)?(.*\S)\s*$")
_NAMED_ITEM = re.compile(r"^(?:\*\*)?([A-Z][\w'-]*)(?::\*\*|\*\*:|:)\s+(.*)$")
_TASK_ID = re.compile(r"^([A-Z]{1,4}\d+[a-z]?)\b")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


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


def roster_section(profile_text: str) -> str | None:
    """The profile's people section, or ``None`` when it declares no contributors."""
    match = re.search(
        r"^## Identity and people\s*$([\s\S]*?)(?=^## |\Z)",
        profile_text,
        re.MULTILINE,
    )
    if not match or "contributors" not in match.group(1).casefold():
        return None
    return match.group(1)


def roster_contains(profile_text: str, contributor: str) -> bool | None:
    """Check the contributor roster, or return ``None`` when no roster is declared."""
    roster = roster_section(profile_text)
    if not contributor or roster is None:
        return None
    # Whole name only. A substring test makes "Al" a member of a roster listing Alice.
    bounded = rf"(?<![\w-]){re.escape(contributor)}(?![\w-])"
    return re.search(bounded, roster, re.IGNORECASE) is not None


def resolve_state(root: Path, profile: dict[str, str], contributor: str) -> Path | None:
    """Resolve one contributor state file without opening every candidate.

    Returns ``None`` rather than guessing. A wrong state file is worse than none, because
    nothing downstream can tell it apart from the right one.
    """
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

    # NO SINGLETON FALLBACK. This used to end `return candidates[0] if len(candidates) == 1
    # else None`, so in a repository holding one state file *every* contributor resolved to
    # it. Measured on a three-person roster: two teammates each received the third person's
    # branch, evidence and next action, on a card headed with their own name. A convenience
    # for the first contributor turns into silent misattribution for the second, and the
    # state convention's one-writer rule cannot survive it.
    #
    # The slug-bounded match above stays: a contributor whose slug is `dana` still finds
    # `dana-reed.md`, while one whose slug appears in no filename finds nothing. An empty
    # result is the right answer, because a missing state file is the normal condition
    # before a contributor has written one.
    return None


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


def claim_name(claimed_by: str) -> str:
    """The person part of a claim, which by convention carries its branch after an em dash.

    The em dash is matched bare, so a tight ``<name>—<branch>`` ends the name too. That is how
    ``tools/ticket_status.py`` reads the same field, and a reader that required the spaces would
    disagree with the board about where the name ends for a claim written without them -- which
    is the defect this helper exists to close, in a narrower form.
    """
    value = one_line(claimed_by)
    for separator in ("—", " -- "):
        if separator in value:
            return value.split(separator, 1)[0].strip()
    return value


def same_person(claimed_by: str, contributor: str) -> bool:
    """Compare a claim against full-name, first-name, and state-file conventions.

    The claim is a field, not a name: `docs/sdd-workflow.md` writes it `<name — branch>`, so the
    branch is dropped before comparing. Keeping it made every ticket claimed the documented way
    read as foreign, and printed the same person on both sides of "not".
    """
    claim = claim_name(claimed_by).casefold()
    person = one_line(contributor).casefold()
    if claim in _NONE:
        return True
    first = person.split()[0] if person.split() else ""
    return claim in {person, first, contributor_slug(contributor)}


def plain(text: str) -> str:
    """Roadmap text without bold or link markup; the words themselves are untouched."""
    return one_line(_LINK.sub(r"\1", text).replace("**", ""))


def month_days(text: str) -> list[tuple[int, int]]:
    """Every real month-and-day in ``text``, in order. The year is resolved separately."""
    found: list[tuple[int, int]] = []
    for name, day in _MONTH_DAY.findall(text):
        month = _MONTHS.index(name[:3].casefold()) + 1
        try:
            date(2000, month, int(day))  # a leap year, so only an impossible day fails
        except ValueError:
            continue
        found.append((month, int(day)))
    return found


def _on(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError:  # Feb 29 outside a leap year, the only day `month_days` lets through
        return date(year, month, 28)


def resolve_dates(pairs: list[tuple[int, int]], today: date) -> list[date]:
    """Give a roadmap's year-less dates their years, in document order.

    A roadmap writes "Oct 26", not "2026-10-26". The first date takes the latest year that puts
    it no more than a quarter past today, so a plan that starts soon and one that started months
    ago both anchor. Each later date takes the year nearest the date before it, which crosses the
    new year and survives a nested heading that steps back in time. Nearest-to-today alone fails
    on any plan longer than six months: seen from October, "Apr 30" is nearer last April.
    """
    resolved: list[date] = []
    for month, day in pairs:
        if resolved:
            previous = resolved[-1]
            years = (previous.year - 1, previous.year, previous.year + 1)
            candidates = [_on(year, month, day) for year in years]
            resolved.append(min(candidates, key=lambda d: abs(d - previous)))
        else:
            ceiling = today + timedelta(days=92)
            candidate = _on(ceiling.year, month, day)
            resolved.append(
                candidate if candidate <= ceiling else _on(ceiling.year - 1, month, day)
            )
    return resolved


def sections(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """Each heading's level, text, and the lines it owns up to the next heading as high."""
    heads = [
        (index, len(match.group(1)), match.group(2))
        for index, line in enumerate(lines)
        if (match := _HEADING.match(line))
    ]
    result: list[tuple[int, str, list[str]]] = []
    for position, (index, level, text) in enumerate(heads):
        end = next((i for i, lv, _ in heads[position + 1 :] if lv <= level), len(lines))
        result.append((level, text, lines[index + 1 : end]))
    return result


def week_items(body: list[str]) -> list[tuple[str, bool, str]]:
    """``(owner, done, text)`` for each top-level list item in a week.

    An item belongs to a ``Name:`` prefix when it carries one, and otherwise to the first word
    of the subheading above it. A subheading that is not a person, such as exit criteria, owns
    items too; they carry no task ID and match no contributor, so they surface nowhere.
    """
    owner = ""
    items: list[tuple[str, bool, str]] = []
    for line in body:
        if heading := _HEADING.match(line):
            owner = next(iter(re.findall(r"[^\W\d_][\w'-]*", heading.group(2))), "")
            continue
        if not (item := _ITEM.match(line)):
            continue
        box, text = item.groups()
        named = _NAMED_ITEM.match(text)
        who, text = (named.group(1), named.group(2)) if named else (owner, text)
        items.append((who, box in ("x", "X"), plain(text)))
    return items


def week_block(
    text: str,
    shown: str,
    contributor: str,
    today: date,
    roster: str | None = None,
    max_chars: int = WEEK_MAX_CHARS,
) -> str:
    """Render the roadmap week containing ``today`` for one contributor, under its own budget.

    Returns an empty string when the roadmap has no dated week headings, which is a roadmap
    kept in another shape rather than a defect. Like the card, a task is listed whole or
    counted, never cut.
    """
    parsed = sections(text.splitlines())
    weeks = [
        (level, title, body, pair)
        for level, title, body in parsed
        if (match := _WEEK_TITLE.match(title)) and len(pair := month_days(match.group(1))) == 2
    ]
    if not weeks:
        return ""
    spans = resolve_dates([md for *_, pair in weeks for md in pair], today)

    rows = [
        (plain(cells[0]), found[0])
        for level, title, body in parsed
        if re.match(r"milestones\b", title, re.IGNORECASE)
        for line in body
        if line.lstrip().startswith("|")
        and len(cells := [cell.strip() for cell in line.strip().strip("|").split("|")]) >= 2
        and (found := month_days(cells[1]))
    ]
    dated = zip((name for name, _ in rows), resolve_dates([md for _, md in rows], today))
    upcoming = sorted((when, name) for name, when in dated if when >= today)

    def countdown(when: date) -> str:
        days = (when - today).days
        return {0: "today", 1: "tomorrow"}.get(days, f"in {days} days")

    ahead = " · ".join(
        f"{name} {when:%a %b} {when.day} ({countdown(when)})"
        for when, name in upcoming[:MILESTONES_AHEAD]
    )
    tail = [f"- **Ahead:** {ahead}"] if ahead else []

    def render(lines: list[str]) -> str:
        return "\n".join(lines) + "\n"

    covering = [
        (spans[2 * n + 1] - spans[2 * n], -level, title, body)
        for n, (level, title, body, _) in enumerate(weeks)
        if spans[2 * n] <= today <= spans[2 * n + 1]
    ]
    if not covering:
        return render(["## This week", f"- No week in `{shown}` covers {today:%Y-%m-%d}.", *tail])
    *_, title, body = min(covering, key=lambda week: week[:2])

    theme = next(
        (m.group(1) for line in body if (m := re.match(r"\*\*Theme:\*\*\s*(.+)", line))), ""
    )
    me = contributor_slug(contributor)
    mine = [
        (done, task) for who, done, task in week_items(body) if me and contributor_slug(who) == me
    ]
    tasks = [f"  - {task}" for done, task in mine if not done]
    done = len(mine) - len(tasks)

    # A teammate is someone the roster names, matched with case: "Week" from an exit-criteria
    # heading once became a lane, and a case-blind match finds it in "onboarding week".
    def teammate(who: str) -> bool:
        named = rf"(?<![\w-]){re.escape(who)}(?![\w-])"
        return roster is None or re.search(named, roster) is not None

    team: dict[str, list[str]] = {}
    for who, finished, task in week_items(body):
        if who and contributor_slug(who) != me and not finished and (tid := _TASK_ID.match(task)):
            if teammate(who):
                team.setdefault(who, []).append(tid.group(1))
    if team:
        lane = " · ".join(f"{who} {', '.join(ids)}" for who, ids in team.items())
        tail.insert(0, f"- **Team:** {lane}")

    lines = [f"## This week — {plain(title)}"] + ([f"- **Theme:** {plain(theme)}"] if theme else [])
    if mine:
        lines.append(f"- **Yours ({len(tasks)} open" + (f", {done} done):**" if done else "):**"))
    else:
        first = contributor.split()[0] if contributor.split() else "you"
        lines.append(f"- **Yours:** nothing listed for {first}")

    more = f"  - +{len(tasks)} more in `{shown}`"  # the widest the overflow line can be
    listed = 0
    for task in tasks:
        reserve = [more] if listed < len(tasks) - 1 else []
        if len(render([*lines, task, *reserve, *tail])) > max_chars:
            break
        lines.append(task)
        listed += 1
    if hidden := len(tasks) - listed:
        lines.append(f"  - +{hidden} more in `{shown}`")

    block = render([*lines, *tail])
    if len(block) > max_chars:
        return render([lines[0], f"- The week is too long for the card; read it in `{shown}`."])
    return block


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
    today: date | None = None,
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
    elif (named := (task or state_ticket)) and path_value(named).casefold() not in _NONE:
        # A none-word is a filled field saying there is no ticket, which is the normal state
        # of a repo before the first one is cut -- and `templates/state.md` tells the writer to
        # put "none" there. `resolve_ticket` already treats it as absent; warning on it made a
        # correctly-written state file report a defect on every session card.
        #
        # NORMALISE THE SAME WAY `resolve_ticket` DOES. This tested the RAW value, so the
        # moment a writer appended the reason -- `none -- planning/tickets/ is empty` --
        # the string stopped matching `_NONE` and the warning came back. Worse, taking
        # this branch skips the `else`, so `Governing agreement` and `Context anchors`
        # were dropped from the card: the session lost exactly the anchors a state file
        # supplies WHEN THERE IS NO TICKET, which is when it needs them most.
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
    diary_path = resolve_diary(root, profile, contributor)
    diary_date = latest_date(diary_path)

    # The diary is not the only clock, and it is not the one that makes state wrong.
    # Comparing state against diary headings alone reported "current" across commits that
    # had reversed the decision the state file still described, because no diary entry had
    # been written in between. Committed work is the other clock.
    #
    # Revision identity, not a calendar date. Asking whether HEAD has moved past the state
    # file's own last commit answers this at any resolution; a `%cs` date reduces it to a
    # day, and most stale state is same-day because that is what a working session looks
    # like. Empty outside git, or before the file is committed, and both fall through to
    # the diary comparison rather than claiming freshness.
    state_rev = (
        git_value(root, "log", "-1", "--format=%H", "--", str(state_path)) if state_path else ""
    )
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

    # The roadmap is reduced to one week inside this process, under its own budget, and is
    # appended after the card so a heavy week can never turn the routing card into a block.
    week = ""
    roadmap = path_value(profile.get("roadmap_path", ""))
    if roadmap.casefold() not in _NONE:
        roadmap_path = root / roadmap
        if roadmap_path.is_file() and contained(root, roadmap_path):
            week = week_block(
                read_text(roadmap_path),
                roadmap,
                contributor,
                today or date.today(),
                roster_section(profile_text),
            )
            if week:
                card.sources.append(roadmap_path)
        else:
            card.warnings.append(
                f"Roadmap {roadmap} does not resolve to a file inside the project."
            )

    return card.render(root, max_chars) + (f"\n{week}" if week else "")


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
