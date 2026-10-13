#!/usr/bin/env python3
"""Derive ticket and spec status from the filesystem, and fail on drift.

Nothing here reads a written status. Doneness is derived by running each ticket's
own check, because a status someone has to remember to update is a status that
goes stale: across three repositories, 95 acceptance boxes were written into specs
and not one was ever ticked.

The exit code is the point. It is non-zero when:

  1. a ticket carries an Outcome but its check fails      -- closed on a lie
  2. a CLOSED ticket's check no longer resolves            -- the path moved
  3. a ticket is blocked by a ticket that does not exist  -- a dangling edge
  4. a component in the spec map has no spec              -- planned, unwritten
  5. a spec directory has no tickets                      -- written, uncut
  6. a ticket or the profile is MALFORMED                 -- the board is blind

Condition 6 is the open-ended one, and deliberately not enumerated above: no check
named, a check written as a full command, an `sme` row absent from the register, an
unknown `check_type`, a `test_command` naming no runner or one that cannot be
launched. What they share is that the board cannot report on the ticket at all, so
-- unlike a check that has simply not been written yet -- they are drift whatever
state the ticket is in.

A repo adopting this workflow mid-flight will have specs that predate ticketing
and will never have tickets. Name them in the profile's `pre_workflow_specs`
rather than weakening condition 5: an explicit list is auditable, and it shrinks
as those specs are retired.

Standard library only, deliberately: this file is vendored into project repos,
and a vendored file with dependencies is a burden on every one of them.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_DEFAULT = Path("planning/agent/profile.md")

# Profile values are prose: `- **key:** <value> -- commentary`. Take the value.
_PROFILE_LINE = re.compile(r"^\s*-\s+\*\*([A-Za-z_][A-Za-z0-9_]*):\*\*\s*(.*)$")
_FIELD = re.compile(r"^\*\*([A-Za-z_][A-Za-z0-9_ ]*):\*\*\s*(.*)$")
_TITLE = re.compile(r"^#\s*(\d+)\s*[-—]+\s*(.+)$")
_MAP_ROW = re.compile(r"^\|\s*([A-Za-z0-9.\-]+)\s*\|([^|]*)\|([^|]*)\|")
_ENV_ASSIGN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")

# What a shell returns for a command IT could not find. Only the command branch reads
# this, where the shell did run and the thing it could not find is the ticket's own
# check. An argv that will not exec is a different event -- see Unlaunchable.
SHELL_COMMAND_NOT_FOUND = 127

NONE_WORDS = {"none", "none (can start immediately)", "-", "—", ""}
COMMAND_CHECK_TYPES = {"gate", "metric", "dataset", "query", "artifact"}
CHECK_TYPES = {"test", "sme", "manual", *COMMAND_CHECK_TYPES}
OUTCOME_PLACEHOLDERS = {"", "#nn", "nn", "n/a", "none", "tbd", "todo", "<pr>"}


def scalar(raw: str) -> str:
    """The value part of a profile or ticket field, with commentary removed."""
    for sep in ("—", " -- "):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    return raw.strip().strip("`").rstrip(".").strip()


def component_of(name: str, ids: set[str], implied: set[str] = frozenset()) -> str:
    """The declared component id that a spec or ticket directory name carries.

    The two trees may name one component differently -- `B.9` for the ticket
    directory, `B.9-report-readiness` for the spec -- because the profile's
    `ticket_dir` pattern says `<spec-id>` without saying which form that is.
    Comparing raw names keys one side by slug and the other by id, so the lookup
    can never hit and cutting a ticket never clears the spec's line.

    Resolve both sides against the ids the repo has DECLARED rather than guessing
    from the string's shape. Guessing is what a hyphen split does, and it cannot
    tell `foo-bar-baz` apart from a longer slug for `foo-bar`: it would credit one
    spec with another's tickets and turn that spec's drift line off. A drift
    detector that under-reports has failed at the only thing it does, so a name
    matching no declared id resolves to itself and pairs with nothing but its
    exact twin.

    The longest declared id wins, so `B.8.1-engine` resolves to `B.8.1`, not `B.8`.

    ``implied`` is a second, weaker vocabulary, consulted only for a name the declared
    one does not account for: ticket directory names, which name an id by construction.
    A map that declares some components and not others is the ordinary state of a board
    mid-migration, and with a single vocabulary every undeclared component fell back to
    comparing raw names -- the defect this function exists to close, still open for
    whatever the map had not reached yet.

    **What ``implied`` does NOT do, because the one-way rule below forbids it.** An
    earlier version of this paragraph said ticket directory names "may also be spelled
    with the full slug", which reads as though the slug spelling were handled here. It is
    not. A slug resolves TO a declared id; a bare id never resolves to a slug. So for an
    **undeclared** component whose ticket directory carries the full slug, `known`
    registers `S1-alpha/01` while an edge naming `S1/01` builds exactly that, and the two
    never meet -- the edge is reported dangling against a ticket that exists.

    That is a live over-report, measured, not a hypothetical. It is left alone on purpose:
    closing it needs reverse matching, which the paragraph after next rejects on a
    measured counter-case, and the failure direction is the acceptable one -- a spurious
    drift line is loud and has an obvious remedy, which is declaring the id in the map.
    An under-report would be silent. The remedy is the same one declaration always buys:
    an id in the map's ID column pairs both spellings in both directions.

    ``name in ids`` is checked before the fallback and cannot be folded into it: a
    return value equal to ``name`` means either "declared exactly" or "not declared at
    all", and handing the first case to a weaker vocabulary is how `foo-bar-baz` gets
    absorbed into a declared `foo-bar` and loses its own drift line.

    Resolution runs one way only -- a name may carry an id, never elaborate into one.
    Matching in reverse would pair a bare `B.9` spec directory with a `B.9-report`
    ticket directory, and was measured against the case that forbids it: two spec
    directories `foo-bar` and `foo-bar-baz` with tickets under the longer one only,
    where reverse matching credits `foo-bar` with its sibling's tickets and drops a
    true line. The remedy for either name form is the same, and is declaration: an id
    in the map's ID column pairs both spellings in both directions.
    """
    if name in ids:
        return name
    carried = [i for i in ids if name.startswith(i + "-")]
    if carried:
        return max(carried, key=len)
    return component_of(name, implied) if implied else name


def edge_key(
    blocked_by: str,
    citing_spec: str,
    ids: set[str] | frozenset[str] = frozenset(),
    implied: set[str] | frozenset[str] = frozenset(),
) -> str:
    """The `known` key a `Blocked by:` value names.

    **The spec side is resolved through the component vocabulary**, the same way every
    other spec-to-ticket join in this file is, because the two sides of this comparison
    are written by different hands: `known` is keyed by TICKET DIRECTORY NAME, and a
    `Blocked by:` value is whatever an author typed. A repo whose ticket directories
    carry the full slug (`S1-alpha/`) registers `S1-alpha/01` while an edge naming the
    declared id builds `S1/01`, so a valid edge reported as dangling -- the same class
    of defect as the discarded prefix below, in the half the earlier fix did not reach,
    and missed because its test used the bare-id spelling that happens to work.

    With empty vocabularies this is the identity on the spec side, which is what makes
    the two-argument call still meaningful in isolation.

    Two defects lived in the one expression this replaces,
    `f"{t.spec_id}/{b.split('/')[-1].zfill(2)}"`:

    **It discarded the spec a cross-spec edge named.** `S2/05` blocked by `S1/01` took
    `01` and re-prefixed it with the CITING ticket's spec, looking up `S2/01`. A valid
    edge reported as dangling; worse, where `S2/01` happened to exist the edge validated
    against the wrong ticket and a genuinely dangling edge passed silently.

    **It padded one side only.** A ticket headed `# 1 -` registers as `S1/1`, while an
    edge naming `1` built `S1/01`, so a well-formed set reported drift. The template
    writes both as `NN` without saying the heading must be zero-padded, so the first real
    ticket set could fail the board for nothing. Both sides are normalised now.
    """
    spec, _, number = blocked_by.strip().rpartition("/")
    named = spec.strip() or citing_spec
    return f"{component_of(named, set(ids), set(implied))}/{norm_number(number)}"


def norm_number(number: str) -> str:
    """A ticket number compared the same way wherever it is read.

    Applied to the ticket's own heading AND to every edge naming it, so `1`, `01` and
    `001` are one ticket rather than three. A non-decimal number is left alone rather
    than silently mangled.
    """
    n = number.strip()
    # Compare by VALUE, not by spelling. `zfill` pads but never truncates, so `001`
    # stayed `001` while `1` became `01` -- two keys for one ticket, and every edge
    # naming `1` dangled against a file headed `# 001 -`.
    #
    # `isdecimal`, not `isdigit`: `isdigit` is True for category-No characters such as a
    # superscript two, which `int()` then REJECTS with ValueError -- so a ticket number or
    # a `Blocked by:` value carrying one crashed the board instead of being left alone.
    # Both are author-typed text, so both are reachable.
    return f"{int(n):02d}" if n.isdecimal() else n


def base_dir(pattern: str) -> str:
    """The fixed prefix of a path pattern, above the first placeholder.

    `planning/tickets/<spec-id>/`          -> `planning/tickets`
    `planning/specs/P{N}.{n}-<slug>/spec.md` -> `planning/specs`

    Both placeholder styles occur: `<name>` and `{N}`. Truncating at the
    placeholder is not enough, because a pattern may carry a literal prefix
    inside the final segment -- so fall back to the last complete directory.
    """
    m = re.search(r"[<{]", pattern)
    if not m:  # already a plain directory
        return pattern.rstrip("/")
    head = pattern[: m.start()]
    return head[: head.rfind("/")].rstrip("/") if "/" in head else head.rstrip("/")


def load_profile(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _PROFILE_LINE.match(line)
        if m:
            out.setdefault(m.group(1), scalar(m.group(2)))
    return out


@dataclass
class Ticket:
    path: Path
    spec_id: str
    number: str
    title: str
    check_type: str = "manual"
    check: str = ""
    claimed_by: str = "unclaimed"
    blocked_by: list[str] = field(default_factory=list)
    has_outcome: bool = False
    state: str = "unknown"  # pass | fail | unresolved | unknown | skipped
    detail: str = ""
    # Two kinds of "unresolved" needing different treatment. MALFORMED means the
    # ticket is wrong in itself -- no check named, or a register row that is not
    # there -- and is drift whatever its state. A check that has simply not been
    # written yet is the normal condition of an unstarted ticket, because TDD names
    # the check before the test exists.
    malformed: bool = False

    @property
    def ident(self) -> str:
        return f"{self.spec_id}/{self.number}"


def parse_ticket(path: Path, spec_id: str) -> Ticket:
    text = path.read_text(encoding="utf-8")
    number, title = path.stem.split("-", 1)[0], path.stem
    for line in text.splitlines():
        m = _TITLE.match(line)
        if m:
            number, title = m.group(1), m.group(2).strip()
            break

    t = Ticket(path=path, spec_id=spec_id, number=norm_number(number), title=title)
    body, _, outcome = text.partition("## Outcome")

    for line in body.splitlines():
        m = _FIELD.match(line.strip())
        if not m:
            continue
        key, value = m.group(1).strip().lower().replace(" ", "_"), m.group(2).strip()
        if key == "check_type":
            t.check_type = scalar(value).lower()
        elif key == "check":
            t.check = value.strip().strip("`")
        elif key == "claimed_by":
            t.claimed_by = scalar(value)
        elif key == "blocked_by":
            v = scalar(value).lower()
            if v not in NONE_WORDS:
                t.blocked_by = [p.strip() for p in re.split(r"[,;]", scalar(value)) if p.strip()]

    # An Outcome is real only once the placeholder has been replaced. Older
    # templates shipped `#NN`, which must not close every newly cut ticket.
    pr = re.search(r"^\*\*PR:\*\*\s*(.*)$", outcome, re.M)
    pr_value = scalar(pr.group(1)).lower() if pr else ""
    t.has_outcome = pr_value not in OUTCOME_PLACEHOLDERS
    return t


def collect(ticket_root: Path) -> dict[str, list[Ticket]]:
    out: dict[str, list[Ticket]] = {}
    if not ticket_root.is_dir():
        return out
    for spec_dir in sorted(
        p for p in ticket_root.iterdir() if p.is_dir() and not p.name.startswith(".")
    ):
        tickets = [
            parse_ticket(f, spec_dir.name)
            for f in sorted(spec_dir.glob("*.md"))
            if f.name.lower() != "readme.md"
        ]
        out[spec_dir.name] = tickets
    return out


def is_written_spec(p: Path) -> bool:
    """Has somebody actually written a spec in this directory?

    A DIRECTORY IS NOT A SPEC: counting an empty one as written let `mkdir` turn off the
    "planned in the spec map, no spec written" line the map exists to produce.

    LITTER IS NOT A FILE: `any(p.iterdir())` was satisfied by anything at all, including
    a lone `.ipynb_checkpoints/` or `.DS_Store`, so the same hole survived one layer down.

    AND AN EMPTY FILE IS NOT A SPEC: `touch spec.md` also turned the line off, and that is
    the one of the three that happens BY ACCIDENT -- a scaffolding step or an interrupted
    write leaves exactly a 0-byte `spec.md`. So a spec is written when the directory holds
    a non-dot file with CONTENT in it, checked without assuming the file is named
    `spec.md`, because that name comes from the profile's `spec_path_pattern`.

    An unreadable directory reads as not-written rather than crashing: a traceback in a
    drift detector loses the other fifteen lines along with this one. Note `is_file` and
    `is_dir` FOLLOW SYMLINKS, so a symlink to a file elsewhere counts as a written spec
    and a broken symlink does not -- stated here because it is a choice, not an accident.
    """
    if not p.is_dir() or p.name.startswith("."):
        return False
    try:
        return any(
            f.is_file() and not f.name.startswith(".") and f.stat().st_size > 0 for f in p.iterdir()
        )
    except OSError:
        return False


def parse_spec_map(path: Path) -> list[str]:
    """Component IDs from the map's component table(s).

    Three rules, in order of how much damage getting them wrong does:

    **1. Never lose a real id.** This is a DRIFT DETECTOR: a phantom component produces a
    noisy extra line, which is loud and gets fixed, while a lost component silently stops
    producing the "planned, no spec written" condition for a real component. The first
    attempt at scoping inverted that -- it took the first `ID`-headed table positionally,
    and against three ordinary map shapes it dropped real ids, one of which turned the
    whole board GREEN WITH EXIT 0. So the fallback here is the UNION OF EVERY TABLE, which
    is never narrower than reading the whole file was.

    **2. A fenced block is documentation, not data.** A map that shows its own row format
    in a ``` fence was the exit-0 case: the fence's table came first, its one row read
    `| S<n> | ...` which is not an id, and an empty table won. Fences are skipped.

    **3. A header is not a row, so it is not matched with the row pattern.** `_MAP_ROW`
    requires a first cell of alphanumerics, dots and dashes, which `Spec ID` and `**ID**`
    both fail -- so the
    header line was skipped entirely, the SEPARATOR row became the table's "header" flagged
    not-ID, and a different table won. Headers are split on `|` and normalised instead:
    markup stripped, lower-cased, and a cell counts as an ID column when its words include
    `id`. A header this does not recognise costs nothing, because of rule 1.

    Scoping still does its job: a map with an `ID`-headed component table and a
    "Vocabulary gaps | Term | Why | Owner" table reads only the first, instead of minting
    `Term`, `sponsor` and `intake` as planned components.

    **The trade rule 1 buys, stated so it is not read as absolute:** in a map where NO
    header names an ID column, the union fallback reinstates that noise -- a gaps table
    there does contribute its rows as planned components. The original defect is demoted
    to that one shape rather than eliminated, which is the right way round, because the
    remedy is a header a repo can write and the alternative is silence.
    """
    if not path.is_file():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()

    # Fenced regions, counted ONLY WHERE THE FENCE CLOSES. A plain `fenced = not fenced`
    # toggle reopened the exit-0 path this skipping exists to close: one dropped closing
    # fence swallowed the rest of the file, so a map whose Components table sat below an
    # unterminated ``` block parsed to zero ids and the board printed "no drift", exit 0.
    # An unmatched trailing fence is therefore ignored rather than treated as opening a
    # region to EOF -- rule 1 again, never lose a real id, and here it has to hold even
    # for malformed markdown.
    # Paired BY POSITION, which encodes "the trailing marker is the stray one". That is
    # the right prior: the opener is typed first, so it is the closer that gets dropped.
    #
    # The asymmetry is deliberate and is a choice, not an oversight. Where the stray
    # marker comes FIRST, position-pairing fences from it to the real example fence's
    # opener, so a genuine table can be skipped and an example's ids returned instead.
    # Nothing in the text says which of three markers is the stray, so no rule gets both.
    # This one is chosen because its failure is LOUD -- the example's ids surface as
    # planned components with no spec, so the board is red with a visibly bogus id -- and
    # the other arrangement's failure was the silent exit-0 that this pairing replaced.
    marks = [i for i, raw in enumerate(lines) if raw.strip().startswith(("```", "~~~"))]
    fenced_lines: set[int] = set()
    for opened, closed in zip(marks[::2], marks[1::2]):
        fenced_lines.update(range(opened, closed + 1))

    # Group into tables: maximal runs of pipe-prefixed lines outside fenced regions.
    tables: list[list[str]] = []
    run: list[str] = []
    for i, raw in enumerate(lines):
        if i in fenced_lines:
            if run:
                tables.append(run)
                run = []
            continue
        line = raw.strip()
        if line.startswith("|"):
            run.append(line)
        elif run:
            tables.append(run)
            run = []
    if run:
        tables.append(run)

    declared: list[str] = []
    everything: list[str] = []
    for rows in tables:
        # Markdown requires a header row, so the run's first line is one, never a component.
        head, body = rows[0], rows[1:]
        ids: list[str] = []
        for line in body:
            m = _MAP_ROW.match(line)
            if not m:
                continue
            ident = m.group(1).strip()
            if ident.lower() in {"id", "---"} or set(ident) <= {"-", ":"}:
                continue
            ids.append(ident)
        everything.extend(ids)
        if _is_id_header(head):
            declared.extend(ids)

    chosen = declared or everything
    seen: set[str] = set()
    return [i for i in chosen if not (i in seen or seen.add(i))]


def _is_id_header(line: str) -> bool:
    """Does this header row's FIRST cell name an ID column?

    Split on `|` rather than matched with `_MAP_ROW`, because a header is not a row and
    does not obey a row's content rules: `Spec ID` carries a space and `**ID**` carries
    markup, and both failed the row pattern. Markup is stripped, so `ID`, `**ID**`,
    `Spec ID`, `` `id` `` and `ID#` all count.
    """
    cells = line.strip().strip("|").split("|")
    if not cells:
        return False
    first = re.sub(r"[^a-z0-9 ]+", " ", cells[0].strip().lower())
    return "id" in first.split()


def split_runner(test_command: str) -> tuple[list[str], dict[str, str]]:
    """Split `VAR=value prog args` into an argv and the environment it asked for.

    A `test` check runs without a shell, so a profile that writes its runner the way
    it would be typed at a prompt -- `PYTHONPATH=. python3 -m pytest` -- would
    otherwise be exec'd as a program named literally `PYTHONPATH=.`. Pinning an
    interpreter's path or a config file through the environment is the ordinary way
    to name a runner, so honour the prefix rather than making every host repo
    discover the same failure separately.
    """
    argv = shlex.split(test_command)
    env: dict[str, str] = {}
    while argv and (m := _ENV_ASSIGN.match(argv[0])):
        env[m.group(1)] = m.group(2)
        argv.pop(0)
    return argv, env


class Unlaunchable(Exception):
    """argv[0] does not exist, so nothing ran.

    Raised rather than returned as a status, because 127 is a status a process can
    genuinely exit with: a wrapper script returns it when ITS command is missing.
    Folding the two together would report `test_command not found: 'sh'` about an
    `sh` that is sitting right there, and -- since an unlaunchable runner is
    malformed -- would fail the board over a file that is not missing.
    """


def run(
    cmd: list[str] | str, root: Path, timeout: int, env: dict[str, str] | None = None
) -> tuple[int, str]:
    """Run a check. Raises Unlaunchable if the program itself cannot be exec'd."""
    try:
        # S603: running the check a ticket names IS the job. The checks come from
        # files in the repo, at the same trust level as the code being tested.
        p = subprocess.run(  # noqa: S603
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
            env={**os.environ, **env} if env else None,
        )
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    except FileNotFoundError as exc:
        raise Unlaunchable(str(exc)) from exc
    tail = (p.stderr or p.stdout or "").strip().splitlines()
    return p.returncode, tail[-1] if tail else ""


def evaluate(t: Ticket, root: Path, cfg: dict[str, str], timeout: int, execute: bool) -> None:
    if t.check_type not in CHECK_TYPES:
        allowed = ", ".join(sorted(CHECK_TYPES))
        t.state = "unresolved"
        t.detail = f"unknown check_type {t.check_type!r}; expected one of: {allowed}"
        t.malformed = True
        return
    if t.check_type == "manual":
        t.state, t.detail = "unknown", "manual check, never derived"
        return
    if not t.check:
        t.state, t.detail, t.malformed = "unresolved", "no check named", True
        return

    if t.check_type == "sme":
        register = root / cfg.get("sme_register_path", "")
        if not cfg.get("sme_register_path") or not register.is_file():
            t.state, t.detail, t.malformed = "unresolved", "sme_register_path missing", True
            return
        row = t.check.split("#", 1)[-1]
        rows = register.read_text(encoding="utf-8").splitlines()
        hits = [line for line in rows if row in line]
        if not hits:
            t.state, t.detail, t.malformed = "unresolved", f"no row matching {row!r}", True
            return
        pattern = cfg.get("sme_resolved_pattern", r"\b(resolved|confirmed|answered)\b")
        ok = any(re.search(pattern, hit, re.I) for hit in hits)
        t.state = "pass" if ok else "fail"
        t.detail = "" if ok else "row still open"
        return

    if not execute:
        t.state, t.detail = "skipped", "not run"
        return

    if t.check_type == "test":
        runner, runner_env = split_runner(cfg.get("test_command", "pytest"))
        if not runner:
            t.state, t.detail, t.malformed = "unresolved", "test_command names no runner", True
            return
        # The check is a NODE ID. The runner comes from test_command, so a check that
        # repeats it produces `pytest ... "uv run pytest tests/..."` and fails with a
        # collection error that explains nothing. Name the mistake instead.
        if t.check.split()[0] in {runner[0], *runner}:
            t.state = "unresolved"
            t.detail = "check is a full command; it should be a test node id"
            t.malformed = True
            return
        # A runner that will not launch is a broken profile, not an unwritten test, and
        # it hits every `test` ticket at once. Folding it into "does not collect" reads
        # the whole board as merely not-started-yet and hides the one line that explains
        # why -- so it is malformed, and therefore drift whatever state the tickets are
        # in. Contrast the command branch below, where the thing not found is the
        # ticket's own check and not-yet-written is the honest reading.
        try:
            code, _ = run([*runner, "--collect-only", "-q", t.check], root, timeout, runner_env)
            if code != 0:
                # Including a runner that exits 127 of its own accord: it launched, so
                # what it could not find is the test, not itself.
                t.state, t.detail = "unresolved", "does not collect"
                return
            code, msg = run([*runner, "-q", t.check], root, timeout, runner_env)
        except Unlaunchable:
            t.state = "unresolved"
            t.detail = f"test_command not found: {runner[0]!r}"
            t.malformed = True
            return
    elif t.check_type in COMMAND_CHECK_TYPES:
        try:
            code, msg = run(t.check, root, timeout)
        except Unlaunchable:  # shell=True, so this is the shell itself missing
            t.state, t.detail = "unresolved", "command not found"
            return
        if code == SHELL_COMMAND_NOT_FOUND:
            t.state, t.detail = "unresolved", "command not found"
            return
    else:
        # Unreachable while the guard above and these branches agree. Named rather
        # than left as an `else` that would shell-execute the next type someone adds.
        t.state = "unresolved"
        t.detail = f"no evaluator for check_type {t.check_type!r}"
        t.malformed = True
        return

    t.state = "pass" if code == 0 else "fail"
    t.detail = "" if code == 0 else msg[:90]


def mark(t: Ticket) -> str:
    """A failing check means different things open and closed.

    Open, it means not built yet -- the expected state of most of the board.
    Closed, it means the Outcome claims work that the check does not support,
    which is the failure this script exists to surface. Rendering both as FAIL
    buries the second in a page of the first.
    """
    if t.state == "fail":
        return "FAIL" if t.has_outcome else "open"
    if t.state == "unresolved" and not (t.has_outcome or t.malformed):
        return "todo"  # the check is named, the test is not written yet
    return {"pass": "done", "unresolved": "BROKEN", "unknown": "manual", "skipped": "-"}[t.state]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path("."), help="repository root")
    ap.add_argument("--profile", type=Path, default=None, help="path to profile.md")
    ap.add_argument(
        "--no-run",
        action="store_true",
        help="structure only: resolve paths and edges, run no checks",
    )
    ap.add_argument("--timeout", type=int, default=300, help="seconds per check")
    a = ap.parse_args(argv)

    root = a.root.resolve()
    cfg = load_profile(a.profile or root / PROFILE_DEFAULT)

    ticket_root = root / base_dir(cfg.get("ticket_dir", "planning/tickets"))
    spec_pattern = cfg.get("spec_dir") or cfg.get("spec_path_pattern", "planning/specs")
    spec_root = root / base_dir(spec_pattern)
    spec_map = root / cfg.get("spec_map_path", "planning/spec-map.md")

    by_spec = collect(ticket_root)
    planned = parse_spec_map(spec_map)
    # The vocabulary of component ids, and the spec map is the authority on it: its
    # ID column is where a repo says what its components ARE. Ticket directory names
    # are the weaker source, consulted per name for whatever the map does not account
    # for -- `ticket_dir` is `<spec-id>`, so they name an id by construction, but a
    # repo may spell them with the full slug, and admitting them as equals would let a
    # slug compete with the id it elaborates. Spec directory names never join: they
    # carry slugs, and every spec would then resolve only to itself.
    #
    # Built HERE, above the ticket loop, because the blocking edges need it too: both
    # sides of that comparison have to be spelled in one vocabulary, and keying `known`
    # by raw directory name is what made a cross-spec edge dangle against a ticket
    # sitting right there.
    ids, implied = set(planned), set(by_spec)
    known = {
        f"{component_of(t.spec_id, ids, implied)}/{t.number}" for ts in by_spec.values() for t in ts
    }
    drift: list[str] = []

    for tickets in by_spec.values():
        for t in tickets:
            evaluate(t, root, cfg, a.timeout, execute=not a.no_run)
            # A check that does not resolve YET is the normal state of an unstarted
            # ticket: TDD names the check before the test exists. Only a ticket
            # claiming to be done owes a check that resolves. Failing the board on
            # planned work would punish cutting tickets ahead of time, which is the
            # whole purpose of the blocking edges.
            if t.malformed or (t.state == "unresolved" and t.has_outcome):
                drift.append(
                    f"{t.ident}: check does not resolve" + (f" -- {t.detail}" if t.detail else "")
                )
            if t.has_outcome and t.state == "fail":
                drift.append(
                    f"{t.ident}: closed, but its check fails"
                    + (f" -- {t.detail}" if t.detail else "")
                )
            for b in t.blocked_by:
                if edge_key(b, t.spec_id, ids, implied) not in known:
                    drift.append(f"{t.ident}: blocked by {b!r}, which does not exist")

    # Dot-directories are not specs -- the same rule the ticket root applies above.
    # `.ipynb_checkpoints` beside a spec tree is Jupyter litter, and counting it
    # reports "spec written, no tickets cut" against a directory nobody authored.
    # A DIRECTORY IS NOT A SPEC. Counting an empty one as written let `mkdir` turn off
    # the "planned in the spec map, no spec written" line that the map exists to
    # produce -- the exact asymmetry the ticket side already guards below ("an empty
    # directory must still read as 'no tickets cut'"). A spec directory counts once it
    # holds at least one file, checked without assuming the file is named `spec.md`.
    #
    # LITTER IS NOT A FILE, either. `any(p.iterdir())` was satisfied by anything at all,
    # including a lone `.ipynb_checkpoints/` or `.DS_Store` -- so `mkdir` plus whatever
    # the machine drops in a directory still turned the line off, which is the same
    # defect one layer down. The dot rule that already excludes litter DIRECTORIES from
    # being specs is applied to the contents too: a spec is written when the directory
    # holds a non-dot file, and nothing a tool or an OS leaves behind qualifies.
    written = (
        {p.name for p in spec_root.iterdir() if is_written_spec(p)} if spec_root.is_dir() else set()
    )
    written_ids = {component_of(name, ids, implied) for name in written}
    for ident in planned:
        if ident not in written_ids:
            drift.append(f"{ident}: planned in the spec map, no spec written")
    raw_exempt = re.split(r"[,\s]+", cfg.get("pre_workflow_specs", ""))
    grandfathered = {component_of(s.strip(), ids, implied) for s in raw_exempt if s.strip()}
    # A ticket directory that exists but holds no ticket is NOT cut work, so the
    # truthiness matters: an empty directory must still read as "no tickets cut".
    ticketed = {component_of(name, ids, implied) for name, tickets in by_spec.items() if tickets}
    exempt = []
    for name in sorted(written):
        component = component_of(name, ids, implied)
        if component in ticketed:
            continue
        if component in grandfathered:
            exempt.append(name)
        else:
            drift.append(f"{name}: spec written, no tickets cut")

    for spec_id in sorted(by_spec):
        tickets = by_spec[spec_id]
        done = sum(t.state == "pass" for t in tickets)
        print(f"\n{spec_id}  [{done}/{len(tickets)} done]")
        for t in tickets:
            claim = t.claimed_by if t.claimed_by.lower() != "unclaimed" else "-"
            note = f"  {t.detail}" if t.detail and t.state in {"fail", "unresolved"} else ""
            print(
                f"  {t.number:>3} {t.title[:44]:<44} {mark(t):<7}"
                f" {t.check_type:<7} {claim:<12}{note}"
            )

    total = sum(len(v) for v in by_spec.values())
    plural = "spec" if len(by_spec) == 1 else "specs"
    print(
        f"\n{total} tickets across {len(by_spec)} {plural}"
        f"; {len(planned)} components planned, {len(written)} written"
    )
    if exempt:
        print(f"{len(exempt)} predate ticketing and are exempt: {', '.join(exempt)}")

    if not drift:
        print("no drift")
        return 0

    sys.stdout.flush()  # so the report lands above the drift, not interleaved with it
    print(f"\ndrift ({len(drift)}):", file=sys.stderr)
    for d in drift:
        print(f"  {d}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
