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

A repo adopting this workflow mid-flight will have specs that predate ticketing
and will never have tickets. Name them in the profile's `pre_workflow_specs`
rather than weakening condition 5: an explicit list is auditable, and it shrinks
as those specs are retired.

Standard library only, deliberately: this file is vendored into project repos,
and a vendored file with dependencies is a burden on every one of them.
"""

from __future__ import annotations

import argparse
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

    t = Ticket(path=path, spec_id=spec_id, number=number, title=title)
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


def collect(root: Path, ticket_root: Path) -> dict[str, list[Ticket]]:
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


def parse_spec_map(path: Path) -> list[str]:
    """Component IDs from the map's table. Header and separator rows are skipped."""
    if not path.is_file():
        return []
    ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _MAP_ROW.match(line.strip())
        if not m:
            continue
        ident = m.group(1).strip()
        if ident.lower() in {"id", "---"} or set(ident) <= {"-", ":"}:
            continue
        ids.append(ident)
    return ids


def run(cmd: list[str] | str, root: Path, timeout: int) -> tuple[int, str]:
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
        )
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    except FileNotFoundError as exc:
        return 127, str(exc)
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
        runner = shlex.split(cfg.get("test_command", "pytest"))
        # The check is a NODE ID. The runner comes from test_command, so a check that
        # repeats it produces `pytest ... "uv run pytest tests/..."` and fails with a
        # collection error that explains nothing. Name the mistake instead.
        if t.check.split()[0] in {runner[0], *runner}:
            t.state = "unresolved"
            t.detail = "check is a full command; it should be a test node id"
            t.malformed = True
            return
        code, _ = run([*runner, "--collect-only", "-q", t.check], root, timeout)
        if code != 0:
            t.state, t.detail = "unresolved", "does not collect"
            return
        code, msg = run([*runner, "-q", t.check], root, timeout)
    elif t.check_type in COMMAND_CHECK_TYPES:
        code, msg = run(t.check, root, timeout)
        if code == 127:
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

    by_spec = collect(root, ticket_root)
    known = {t.ident for ts in by_spec.values() for t in ts}
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
                if f"{t.spec_id}/{b.split('/')[-1].zfill(2)}" not in known:
                    drift.append(f"{t.ident}: blocked by {b!r}, which does not exist")

    planned = parse_spec_map(spec_map)
    written = {p.name for p in spec_root.iterdir() if p.is_dir()} if spec_root.is_dir() else set()
    for ident in planned:
        if not any(name.split("-", 1)[0] == ident or name == ident for name in written):
            drift.append(f"{ident}: planned in the spec map, no spec written")
    raw_exempt = re.split(r"[,\s]+", cfg.get("pre_workflow_specs", ""))
    grandfathered = {s.strip() for s in raw_exempt if s.strip()}
    exempt = []
    for name in sorted(written):
        if by_spec.get(name):
            continue
        if name in grandfathered or name.split("-", 1)[0] in grandfathered:
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
