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
# The path insert above must run first, so this import cannot join the block.
import ticket_status as ts  # noqa: E402, I001


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
    def build(
        tickets, *, specs=("P1-thing",), map_rows=("| P1 | a thing | — |",), profile_extra=""
    ):
        (tmp_path / "planning/agent").mkdir(parents=True)
        (tmp_path / "planning/agent/profile.md").write_text(PROFILE.format(extra=profile_extra))
        (tmp_path / "planning/spec-map.md").write_text(SPEC_MAP.format(rows="\n".join(map_rows)))
        for s in specs:
            d = tmp_path / "planning/specs" / s
            d.mkdir(parents=True)
            (d / "spec.md").write_text("# Spec\n")
        for spec_id, items in tickets.items():
            d = tmp_path / "planning/tickets" / spec_id
            d.mkdir(parents=True)
            for i, kw in enumerate(items, start=1):
                kw = {
                    "num": f"{i:02d}",
                    "title": f"thing {i}",
                    "blocked": "none",
                    "ctype": "gate",
                    "check": "true",
                    "claim": "unclaimed",
                    "outcome": "",
                    **kw,
                }
                (d / f"{kw['num']}-thing.md").write_text(TICKET.format(**kw))
        return tmp_path

    return build


def status(root: Path, *args) -> int:
    return ts.main(["--root", str(root), *args])


# --- the unit pieces ------------------------------------------------------


def test_scalar_strips_commentary_and_backticks():
    assert ts.scalar("`planning/tickets/` — one per ticket") == "planning/tickets/"
    assert ts.scalar("`make ticket-status`") == "make ticket-status"


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("planning/tickets/<spec-id>/", "planning/tickets"),
        ("planning/specs/<spec-id>/spec.md", "planning/specs"),
        # A literal prefix inside the final segment: truncating at the placeholder
        # alone would leave `planning/tickets/P`.
        ("planning/tickets/P{N}.{n}-<slug>/", "planning/tickets"),
        ("planning/specs/P{N}.{n}-<slug>/spec.md", "planning/specs"),
        ("planning/specs/", "planning/specs"),
        ("planning/specs", "planning/specs"),
    ],
)
def test_base_dir_finds_the_fixed_prefix(pattern, expected):
    assert ts.base_dir(pattern) == expected


@pytest.mark.parametrize(
    "command,argv,env",
    [
        ("pytest", ["pytest"], {}),
        ("uv run pytest", ["uv", "run", "pytest"], {}),
        ("PYTHONPATH=. python3 -m pytest", ["python3", "-m", "pytest"], {"PYTHONPATH": "."}),
        ("A=1 B=2 pytest", ["pytest"], {"A": "1", "B": "2"}),
        # Only a LEADING run of assignments is environment; the shell stops there too,
        # so a `-p no:x=y` style argument stays an argument.
        ("pytest -o addopts=-q", ["pytest", "-o", "addopts=-q"], {}),
        ("FOO= pytest", ["pytest"], {"FOO": ""}),
        ("", [], {}),
    ],
)
def test_split_runner_separates_the_env_prefix_from_the_argv(command, argv, env):
    assert ts.split_runner(command) == (argv, env)


@pytest.mark.parametrize(
    "name,ids,expected",
    [
        # A declared id names itself; a slug elaborating one resolves to it.
        ("P1", {"P1"}, "P1"),
        ("P1-thing", {"P1"}, "P1"),
        ("B.9-report-readiness", {"B.9"}, "B.9"),
        # A name matching no declared id resolves to ITSELF, so it pairs with
        # nothing but its exact twin. This is what keeps the detector from going
        # quiet: guessing here is how one spec gets credited with another's work.
        ("foo-bar-baz", {"foo-bar", "foo-bar-baz"}, "foo-bar-baz"),
        ("foo-bar-baz", set(), "foo-bar-baz"),
        # The hyphen boundary, which a first-hyphen split would get wrong.
        ("foo-baz", {"foo-bar"}, "foo-baz"),
        ("B.90-other", {"B.9"}, "B.90-other"),
        ("P10", {"P1"}, "P10"),
        # The longest declared id wins, so a dotted child is not read as its parent.
        ("B.8.1-engine", {"B.8", "B.8.1"}, "B.8.1"),
        ("P1-thing-x", {"P1", "P1-thing"}, "P1-thing"),
    ],
)
def test_component_of_resolves_against_declared_ids(name, ids, expected):
    assert ts.component_of(name, ids) == expected


def test_profile_parsing_reads_prose_values(tmp_path):
    p = tmp_path / "profile.md"
    p.write_text(PROFILE.format(extra=""))
    cfg = ts.load_profile(p)
    assert cfg["ticket_dir"] == "planning/tickets/<spec-id>/"
    assert cfg["spec_dir"] == "planning/specs"


def test_spec_map_parser_accepts_kind_and_typed_requirements(tmp_path):
    path = tmp_path / "spec-map.md"
    path.write_text(
        "| ID | Kind | Covers | Blocked by | Requires |\n"
        "|---|---|---|---|---|\n"
        "| F1 | build | loader | — | decision: schema |\n"
        "| E1 | experiment | comparison | F1 | data: evaluation set |\n"
    )
    assert ts.parse_spec_map(path) == ["F1", "E1"]


def test_empty_outcome_heading_is_not_an_outcome(tmp_path):
    f = tmp_path / "01-x.md"
    f.write_text(
        TICKET.format(
            num="01",
            title="x",
            blocked="none",
            ctype="gate",
            check="true",
            claim="unclaimed",
            outcome="",
        )
    )
    assert ts.parse_ticket(f, "P1-thing").has_outcome is False


@pytest.mark.parametrize("placeholder", ["#NN", "TBD", "todo", "none", "n/a", "<PR>"])
def test_outcome_placeholder_is_not_an_outcome(tmp_path, placeholder):
    f = tmp_path / "01-x.md"
    f.write_text(
        TICKET.format(
            num="01",
            title="x",
            blocked="none",
            ctype="gate",
            check="true",
            claim="unclaimed",
            outcome=f"**PR:** {placeholder}\n**Diverged:** nothing",
        )
    )
    assert ts.parse_ticket(f, "P1-thing").has_outcome is False


def test_pr_placeholder_does_not_turn_a_failing_open_ticket_into_drift(project):
    root = project({"P1-thing": [{"check": "false", "outcome": "**PR:** #NN"}]})
    assert status(root) == 0


def test_outcome_counts_once_it_names_a_pr(tmp_path):
    f = tmp_path / "01-x.md"
    f.write_text(
        TICKET.format(
            num="01",
            title="x",
            blocked="none",
            ctype="gate",
            check="true",
            claim="dana",
            outcome="**PR:** #12\n**Diverged:** nothing",
        )
    )
    t = ts.parse_ticket(f, "P1-thing")
    assert t.has_outcome and t.claimed_by == "dana"


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


def test_ticket_with_no_check_is_drift(project, capsys):
    root = project({"P1-thing": [{"check": ""}]})
    assert status(root) == 1
    assert "no check named" in capsys.readouterr().err


def test_dangling_blocking_edge_is_drift(project, capsys):
    root = project({"P1-thing": [{"blocked": "07"}]})
    assert status(root) == 1
    assert "does not exist" in capsys.readouterr().err


def test_planned_component_with_no_spec_is_drift(project, capsys):
    root = project({"P1-thing": [{}]}, map_rows=["| P1 | a thing | — |", "| P2 | unwritten | P1 |"])
    assert status(root) == 1
    assert "no spec written" in capsys.readouterr().err


def test_spec_with_no_tickets_is_drift(project, capsys):
    root = project(
        {"P1-thing": [{}]},
        specs=("P1-thing", "P2-other"),
        map_rows=["| P1 | a thing | — |", "| P2 | other | P1 |"],
    )
    assert status(root) == 1
    assert "no tickets cut" in capsys.readouterr().err


# --- check types ----------------------------------------------------------


def test_manual_check_is_unknown_and_never_drift(project, capsys):
    root = project({"P1-thing": [{"ctype": "manual", "check": "eyeball it"}]})
    assert status(root) == 0
    assert "manual" in capsys.readouterr().out


@pytest.mark.parametrize("ctype", ["gate", "metric", "dataset", "query", "artifact"])
def test_command_check_types_run_their_command(project, ctype):
    root = project({"P1-thing": [{"ctype": ctype, "check": "true"}]})
    assert status(root) == 0


def test_unknown_check_type_is_drift(project, capsys):
    root = project({"P1-thing": [{"ctype": "vibes", "check": "true"}]})
    assert status(root) == 1
    assert "unknown check_type" in capsys.readouterr().err


def test_sme_row_resolved_passes(project):
    root = project(
        {"P1-thing": [{"ctype": "sme", "check": "register.md#Q4"}]},
        profile_extra="- **sme_register_path:** `register.md`",
    )
    (root / "register.md").write_text("| Q4 | does it apply | resolved 2026-01-01 |\n")
    assert status(root) == 0


def test_sme_row_still_open_fails_but_is_not_drift_until_closed(project):
    root = project(
        {"P1-thing": [{"ctype": "sme", "check": "register.md#Q4"}]},
        profile_extra="- **sme_register_path:** `register.md`",
    )
    (root / "register.md").write_text("| Q4 | does it apply | pending |\n")
    assert status(root) == 0  # open and failing is fine


def test_sme_row_missing_is_drift(project, capsys):
    root = project(
        {"P1-thing": [{"ctype": "sme", "check": "register.md#Q9"}]},
        profile_extra="- **sme_register_path:** `register.md`",
    )
    (root / "register.md").write_text("| Q4 | other | resolved |\n")
    assert status(root) == 1
    assert "no row matching" in capsys.readouterr().err


def test_test_type_uses_the_configured_runner(project):
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
        profile_extra="- **test_command:** `true`",
    )
    assert status(root) == 0


def test_test_type_that_does_not_collect_yet_is_todo_not_drift(project, capsys):
    """The test is named before it is written. That is TDD, not breakage."""
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/gone.py::test_y"}]},
        profile_extra="- **test_command:** `false`",
    )
    assert status(root) == 0
    assert "todo" in capsys.readouterr().out


def test_closed_test_type_that_does_not_collect_is_drift(project, capsys):
    root = project(
        {
            "P1-thing": [
                {"ctype": "test", "check": "tests/gone.py::test_y", "outcome": "**PR:** #5"}
            ]
        },
        profile_extra="- **test_command:** `false`",
    )
    assert status(root) == 1
    assert "does not resolve" in capsys.readouterr().err


def test_no_run_skips_execution_but_keeps_structural_checks(project, capsys):
    root = project({"P1-thing": [{"check": "false", "outcome": "**PR:** #3"}, {"blocked": "09"}]})
    assert status(root, "--no-run") == 1
    err = capsys.readouterr().err
    assert "does not exist" in err  # structural drift still caught
    assert "check fails" not in err  # nothing was run, so nothing failed


def test_missing_ticket_tree_is_not_a_crash(tmp_path):
    (tmp_path / "planning").mkdir()
    assert status(tmp_path) == 0


def test_open_failing_ticket_reads_as_open_not_failed(project, capsys):
    """Most of a live board is open. Rendering that as FAIL buries the real one."""
    root = project({"P1-thing": [{"check": "false"}, {"check": "false", "outcome": "**PR:** #3"}]})
    assert status(root) == 1
    out = capsys.readouterr().out
    assert "open" in out and "FAIL" in out


def test_one_spec_is_not_pluralised(project, capsys):
    status(project({"P1-thing": [{}]}))
    assert "across 1 spec;" in capsys.readouterr().out


def test_pre_workflow_spec_is_exempt_from_the_no_tickets_check(project, capsys):
    """A repo adopting this mid-flight has specs that will never have tickets."""
    root = project(
        {"P1-thing": [{}]},
        specs=("P1-thing", "P0.9-legacy"),
        map_rows=["| P1 | a thing | — |", "| P0.9 | legacy | — |"],
        profile_extra="- **pre_workflow_specs:** `P0.9`",
    )
    assert status(root) == 0
    assert "predate ticketing" in capsys.readouterr().out


def test_tickets_cut_under_the_bare_id_clear_the_spec_line(project, capsys):
    """The regression: cutting a ticket did not clear "spec written, no tickets cut".

    `ticket_dir` is `planning/tickets/<spec-id>/` and the profile never says which
    form `<spec-id>` takes, so a repo may name the ticket directory `P1` while the
    spec directory carries the slug. Keying one side by each made the lookup miss,
    and the line stayed up no matter how many tickets were cut.
    """
    root = project({"P1": [{}]}, specs=("P1-thing",))
    assert status(root) == 0
    assert "no tickets cut" not in capsys.readouterr().err


def test_the_reverse_naming_also_resolves(project, capsys):
    """Spec directory on the bare id, ticket directory carrying the slug."""
    root = project({"P1-thing": [{}]}, specs=("P1",), map_rows=["| P1 | a thing | — |"])
    assert status(root) == 0
    assert "no tickets cut" not in capsys.readouterr().err


def test_a_neighbouring_slug_is_not_credited_with_another_spec_s_tickets(project, capsys):
    """`foo-bar` and `foo-baz` share a first hyphen, not a component."""
    root = project(
        {"foo-bar": [{}]},
        specs=("foo-bar", "foo-baz"),
        map_rows=["| foo-bar | a | — |", "| foo-baz | b | — |"],
    )
    assert status(root) == 1
    err = capsys.readouterr().err
    assert "foo-baz: spec written, no tickets cut" in err
    assert "foo-bar: spec written" not in err


def test_a_longer_slug_is_not_credited_with_a_shorter_one_s_tickets(project, capsys):
    """`foo-bar-baz` is its own component, not a longer slug for `foo-bar`.

    Resolving by string shape would pair them and clear the line for a spec that
    has no tickets at all -- trading the false positive this branch fixes for a
    false negative, which in a drift detector is the worse of the two: a wrong
    line gets investigated, a missing one never does.
    """
    root = project(
        {"foo-bar": [{}]},
        specs=("foo-bar", "foo-bar-baz"),
        map_rows=["| foo-bar | a | — |", "| foo-bar-baz | b | — |"],
    )
    assert status(root) == 1
    err = capsys.readouterr().err
    assert "foo-bar-baz: spec written, no tickets cut" in err
    assert "foo-bar: spec written" not in err


def test_a_planned_component_whose_spec_is_missing_is_still_reported(project, capsys):
    """The same over-reach on the other condition: a written `foo-bar` must not
    answer for a planned `foo-bar-baz` that nobody wrote."""
    root = project(
        {"foo-bar": [{}]},
        specs=("foo-bar",),
        map_rows=["| foo-bar | a | — |", "| foo-bar-baz | b | — |"],
    )
    assert status(root) == 1
    assert "foo-bar-baz: planned in the spec map, no spec written" in capsys.readouterr().err


def test_ticket_directory_names_stand_in_when_there_is_no_spec_map(project, capsys):
    """`ticket_dir` is `<spec-id>`, so those names are ids by construction.

    Without a map there is no declared vocabulary, and falling back to them is what
    keeps the two name forms pairing for a repo that has not written one.
    """
    root = project({"P1": [{}]}, specs=("P1-thing",), map_rows=[])
    assert status(root) == 0
    assert "no tickets cut" not in capsys.readouterr().err


def test_an_empty_ticket_directory_is_still_uncut(project, capsys):
    """A directory someone made and never filled is not cut work."""
    root = project({"P1-thing": []}, specs=("P1-thing",))
    assert status(root) == 1
    assert "P1-thing: spec written, no tickets cut" in capsys.readouterr().err


def test_exemption_resolves_across_the_two_name_forms(project, capsys):
    """`pre_workflow_specs` names an id; the spec directory carries the slug."""
    root = project(
        {"P1-thing": [{}]},
        specs=("P1-thing", "P0.9-legacy"),
        map_rows=["| P1 | a thing | — |", "| P0.9 | legacy | — |"],
        profile_extra="- **pre_workflow_specs:** `P0.9`",
    )
    assert status(root) == 0
    assert "predate ticketing" in capsys.readouterr().out


def test_without_the_exemption_it_is_still_drift(project, capsys):
    root = project(
        {"P1-thing": [{}]},
        specs=("P1-thing", "P0.9-legacy"),
        map_rows=["| P1 | a thing | — |", "| P0.9 | legacy | — |"],
    )
    assert status(root) == 1
    assert "no tickets cut" in capsys.readouterr().err


def test_unstarted_ticket_whose_check_is_not_written_yet_is_not_drift(project, capsys):
    """TDD names the check before the test exists. That is planning, not breakage."""
    root = project({"P1-thing": [{"check": "definitely-not-a-command-xyz"}]})
    assert status(root) == 0
    assert "todo" in capsys.readouterr().out


def test_closed_ticket_whose_check_vanished_is_drift(project, capsys):
    root = project(
        {"P1-thing": [{"check": "definitely-not-a-command-xyz", "outcome": "**PR:** #9"}]}
    )
    assert status(root) == 1
    assert "does not resolve" in capsys.readouterr().err


def test_test_check_written_as_a_full_command_is_named_as_malformed(project, capsys):
    """The runner comes from test_command; repeating it yields a useless error."""
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "pytest tests/x.py::test_y"}]},
        profile_extra="- **test_command:** `pytest`",
    )
    assert status(root) == 1
    assert "should be a test node id" in capsys.readouterr().err


def test_runner_env_prefix_reaches_the_runner(project, capsys):
    """`VAR=value prog` is how a runner is written; the checks run without a shell."""
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
        profile_extra="""- **test_command:** `FOO=bar sh -c 'test "$FOO" = bar'`""",
    )
    assert status(root) == 0
    # The count, not the word: `[0/1 done]` prints on every board, so a substring
    # match on "done" alone passes even when the runner never launched.
    assert "[1/1 done]" in capsys.readouterr().out  # only reachable if FOO arrived set


def test_unlaunchable_runner_is_named_and_not_blamed_on_the_test(project, capsys):
    """The regression: exec'ing `PYTHONPATH=. python3` read as "the test is missing".

    A runner that cannot start fails every `test` ticket identically, so reporting it
    as a collection failure renders a whole board as todo and says nothing about why.
    It is the profile that is broken, so it is drift even with no ticket closed.
    """
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
        profile_extra="- **test_command:** `definitely-not-a-runner-xyz`",
    )
    assert status(root) == 1
    out, err = capsys.readouterr()
    assert "test_command not found: 'definitely-not-a-runner-xyz'" in err
    assert "does not collect" not in err
    assert "BROKEN" in out and "todo" not in out


def test_runner_that_exits_127_is_not_reported_as_a_missing_runner(project, capsys):
    """127 is a status a process returns, not only one execvp implies.

    A wrapper script -- which the profile template recommends for anything needing a
    shell -- exits 127 when ITS command is missing. The wrapper is not missing, so
    blaming it names a file that is sitting right there, and because an unlaunchable
    runner is malformed, it would fail the board over that false claim.
    """
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
        profile_extra="""- **test_command:** `sh -c 'exit 127'`""",
    )
    assert status(root) == 0  # open ticket whose test is not written: not drift
    out, err = capsys.readouterr()
    assert "not found" not in err
    assert "todo" in out


def test_unlaunchable_is_raised_not_returned_as_a_status(tmp_path):
    """The seam finding #1 turned on: exec failure cannot collide with an exit code."""
    with pytest.raises(ts.Unlaunchable):
        ts.run(["definitely-not-a-runner-xyz"], tmp_path, 30)
    # A real 127 still comes back as an ordinary status.
    assert ts.run("exit 127", tmp_path, 30)[0] == ts.SHELL_COMMAND_NOT_FOUND


def test_empty_test_command_is_named_not_crashed_on(project, capsys):
    """`shlex.split("")` is `[]`, and `runner[0]` on that used to be an IndexError."""
    root = project(
        {"P1-thing": [{"ctype": "test", "check": "tests/x.py::test_y"}]},
        profile_extra="- **test_command:** `` ",
    )
    assert status(root) == 1
    assert "names no runner" in capsys.readouterr().err


def test_dot_directories_are_not_specs(project, capsys):
    """Jupyter and friends leave .ipynb_checkpoints inside the ticket tree."""
    root = project({"P1-thing": [{}]})
    junk = root / "planning/tickets/.ipynb_checkpoints"
    junk.mkdir()
    (junk / "README-checkpoint.md").write_text("# stale\n")
    assert status(root) == 0
    assert ".ipynb_checkpoints" not in capsys.readouterr().out
