"""Tests for tools/ticket_status.py.

The script is what every other part of the workflow trusts to say whether work is
done, so its failure modes are tested directly rather than inferred. Checks use
`gate` with shell builtins so the suite stays fast and needs nothing installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import ticket_status as ts  # noqa: E402


TICKET = """# {num} — {title}

**What becomes true:** something.
**Blocked by:** {blocked}
**Governs:** contracts §1
**check_type:** {ctype}
**check:** `{check}`
**Claimed by:** {claim}

## Approach (non-binding, ≤150 words)

- a hint

## Outcome

{outcome}
"""

PROFILE = """# Agent profile

## Specs, tickets and decisions

- **spec_map_path:** `planning/spec-map.md` — the planned set
- **spec_dir:** `planning/specs`
- **ticket_dir:** `planning/tickets/<spec-id>/` — `NN-slug.md`, one per ticket
{extra}
"""

SPEC_MAP = """# Spec map

| ID | Covers | Blocked by |
|---|---|---|
{rows}
"""


@pytest.fixture
def project(tmp_path: Path):
    def build(tickets, *, specs=("P1-thing",), map_rows=("| P1 | a thing | — |",),
              profile_extra=""):
        (tmp_path / "planning/agent").mkdir(parents=True)
        (tmp_path / "planning/agent/profile.md").write_text(
            PROFILE.format(extra=profile_extra))
        (tmp_path / "planning/spec-map.md").write_text(
            SPEC_MAP.format(rows="\n".join(map_rows)))
        for s in specs:
            d = tmp_path / "planning/specs" / s
            d.mkdir(parents=True)
            (d / "spec.md").write_text("# Spec\n")
        for spec_id, items in tickets.items():
            d = tmp_path / "planning/tickets" / spec_id
            d.mkdir(parents=True)
            for i, kw in enumerate(items, start=1):
                kw = {"num": f"{i:02d}", "title": f"thing {i}", "blocked": "none",
                      "ctype": "gate", "check": "true", "claim": "unclaimed",
                      "outcome": "", **kw}
                (d / f"{kw['num']}-thing.md").write_text(TICKET.format(**kw))
        return tmp_path
    return build


def status(root: Path, *args) -> int:
    return ts.main(["--root", str(root), *args])


# --- the unit pieces ------------------------------------------------------

def test_scalar_strips_commentary_and_backticks():
    assert ts.scalar("`planning/tickets/` — one per ticket") == "planning/tickets/"
    assert ts.scalar("`make ticket-status`") == "make ticket-status"


@pytest.mark.parametrize("pattern,expected", [
    ("planning/tickets/<spec-id>/", "planning/tickets"),
    ("planning/specs/<spec-id>/spec.md", "planning/specs"),
    # A literal prefix inside the final segment: truncating at the placeholder
    # alone would leave `planning/tickets/P`.
    ("planning/tickets/P{N}.{n}-<slug>/", "planning/tickets"),
    ("planning/specs/P{N}.{n}-<slug>/spec.md", "planning/specs"),
    ("planning/specs/", "planning/specs"),
    ("planning/specs", "planning/specs"),
])
def test_base_dir_finds_the_fixed_prefix(pattern, expected):
    assert ts.base_dir(pattern) == expected


def test_profile_parsing_reads_prose_values(tmp_path):
    p = tmp_path / "profile.md"
    p.write_text(PROFILE.format(extra=""))
    cfg = ts.load_profile(p)
    assert cfg["ticket_dir"] == "planning/tickets/<spec-id>/"
    assert cfg["spec_dir"] == "planning/specs"


def test_empty_outcome_heading_is_not_an_outcome(tmp_path):
    f = tmp_path / "01-x.md"
    f.write_text(TICKET.format(num="01", title="x", blocked="none", ctype="gate",
                               check="true", claim="unclaimed", outcome=""))
    assert ts.parse_ticket(f, "P1-thing").has_outcome is False


def test_outcome_counts_once_it_names_a_pr(tmp_path):
    f = tmp_path / "01-x.md"
    f.write_text(TICKET.format(num="01", title="x", blocked="none", ctype="gate",
                               check="true", claim="ahmad", outcome="**PR:** #12\n**Diverged:** nothing"))
    t = ts.parse_ticket(f, "P1-thing")
    assert t.has_outcome and t.claimed_by == "ahmad"


# --- the exit code, which is the point ------------------------------------

def test_clean_project_exits_zero(project, capsys):
    root = project({"P1-thing": [{}, {"blocked": "01"}]})
    assert status(root) == 0
    assert "no drift" in capsys.readouterr().out


def test_closed_ticket_whose_check_fails_is_drift(project, capsys):
    root = project({"P1-thing": [{"check": "false", "outcome": "**PR:** #3"}]})
    assert status(root) == 1
    assert "closed, but its check fails" in capsys.readouterr().err


def test_open_ticket_whose_check_fails_is_not_drift(project):
    """An unfinished ticket is expected to fail. Only a closed one is a lie."""
    assert status(project({"P1-thing": [{"check": "false"}]})) == 0


def test_unresolvable_check_is_drift(project, capsys):
    root = project({"P1-thing": [{"check": "definitely-not-a-command-xyz"}]})
    assert status(root) == 1
    assert "does not resolve" in capsys.readouterr().err


def test_ticket_with_no_check_is_drift(project, capsys):
    root = project({"P1-thing": [{"check": ""}]})
    assert status(root) == 1
    assert "no check named" in capsys.readouterr().err


def test_dangling_blocking_edge_is_drift(project, capsys):
    root = project({"P1-thing": [{"blocked": "07"}]})
    assert status(root) == 1
    assert "does not exist" in capsys.readouterr().err


def test_planned_component_with_no_spec_is_drift(project, capsys):
    root = project({"P1-thing": [{}]},
                   map_rows=["| P1 | a thing | — |", "| P2 | unwritten | P1 |"])
    assert status(root) == 1
    assert "no spec written" in capsys.readouterr().err


def test_spec_with_no_tickets_is_drift(project, capsys):
    root = project({"P1-thing": [{}]}, specs=("P1-thing", "P2-other"),
                   map_rows=["| P1 | a thing | — |", "| P2 | other | P1 |"])
    assert status(root) == 1
    assert "no tickets cut" in capsys.readouterr().err


# --- check types ----------------------------------------------------------

def test_manual_check_is_unknown_and_never_drift(project, capsys):
    root = project({"P1-thing": [{"ctype": "manual", "check": "eyeball it"}]})
    assert status(root) == 0
    assert "manual" in capsys.readouterr().out


def test_sme_row_resolved_passes(project):
    root = project({"P1-thing": [{"ctype": "sme", "check": "register.md#Q4"}]},
                   profile_extra="- **sme_register_path:** `register.md`")
    (root / "register.md").write_text("| Q4 | does it apply | resolved 2026-01-01 |\n")
    assert status(root) == 0


def test_sme_row_still_open_fails_but_is_not_drift_until_closed(project):
    root = project({"P1-thing": [{"ctype": "sme", "check": "register.md#Q4"}]},
                   profile_extra="- **sme_register_path:** `register.md`")
    (root / "register.md").write_text("| Q4 | does it apply | pending |\n")
    assert status(root) == 0  # open and failing is fine


def test_sme_row_missing_is_drift(project, capsys):
    root = project({"P1-thing": [{"ctype": "sme", "check": "register.md#Q9"}]},
                   profile_extra="- **sme_register_path:** `register.md`")
    (root / "register.md").write_text("| Q4 | other | resolved |\n")
    assert status(root) == 1
    assert "no row matching" in capsys.readouterr().err


def test_test_type_uses_the_configured_runner(project):
    root = project({"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
                   profile_extra="- **test_command:** `true`")
    assert status(root) == 0


def test_test_type_that_does_not_collect_is_drift(project, capsys):
    root = project({"P1-thing": [{"ctype": "test", "check": "tests/gone.py::test_y"}]},
                   profile_extra="- **test_command:** `false`")
    assert status(root) == 1
    assert "does not collect" in capsys.readouterr().err


def test_no_run_skips_execution_but_keeps_structural_checks(project, capsys):
    root = project({"P1-thing": [{"check": "false", "outcome": "**PR:** #3"},
                                 {"blocked": "09"}]})
    assert status(root, "--no-run") == 1
    err = capsys.readouterr().err
    assert "does not exist" in err          # structural drift still caught
    assert "check fails" not in err         # nothing was run, so nothing failed


def test_missing_ticket_tree_is_not_a_crash(tmp_path):
    (tmp_path / "planning").mkdir()
    assert status(tmp_path) == 0


def test_open_failing_ticket_reads_as_open_not_failed(project, capsys):
    """Most of a live board is open. Rendering that as FAIL buries the real one."""
    root = project({"P1-thing": [{"check": "false"},
                                 {"check": "false", "outcome": "**PR:** #3"}]})
    assert status(root) == 1
    out = capsys.readouterr().out
    assert "open" in out and "FAIL" in out


def test_one_spec_is_not_pluralised(project, capsys):
    status(project({"P1-thing": [{}]}))
    assert "across 1 spec;" in capsys.readouterr().out


def test_pre_workflow_spec_is_exempt_from_the_no_tickets_check(project, capsys):
    """A repo adopting this mid-flight has specs that will never have tickets."""
    root = project({"P1-thing": [{}]}, specs=("P1-thing", "P0.9-legacy"),
                   map_rows=["| P1 | a thing | — |", "| P0.9 | legacy | — |"],
                   profile_extra="- **pre_workflow_specs:** `P0.9`")
    assert status(root) == 0
    assert "predate ticketing" in capsys.readouterr().out


def test_without_the_exemption_it_is_still_drift(project, capsys):
    root = project({"P1-thing": [{}]}, specs=("P1-thing", "P0.9-legacy"),
                   map_rows=["| P1 | a thing | — |", "| P0.9 | legacy | — |"])
    assert status(root) == 1
    assert "no tickets cut" in capsys.readouterr().err
