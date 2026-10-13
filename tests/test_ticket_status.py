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


@pytest.mark.parametrize(
    "name,ids,implied,expected",
    [
        # A name the map does not account for falls through to the weaker vocabulary,
        # which is what makes a PARTIALLY written map resolve per component instead of
        # all-or-nothing. A map naming some components is the normal state of a board.
        ("B.9-report", set(), {"B.9"}, "B.9"),
        ("B.9-report", {"P1"}, {"B.9"}, "B.9"),
        # The declared tier wins outright: a prefix match there beats an exact match in
        # the weaker one, or a slug spelled into a ticket directory would compete with
        # the id it elaborates.
        ("P1-thing", {"P1"}, {"P1-thing"}, "P1"),
        # Declared exactly, so the fallback is never consulted. Folding this into the
        # "resolved == name" test is how `foo-bar-baz` gets absorbed into `foo-bar`.
        ("foo-bar-baz", {"foo-bar", "foo-bar-baz"}, {"foo-bar"}, "foo-bar-baz"),
        # Resolution runs one way. A name carries an id; it never elaborates into one,
        # so a bare spec directory cannot reach a slugged ticket directory. Matching in
        # reverse would credit `foo-bar` with a sibling `foo-bar-baz`'s tickets.
        ("B.9", set(), {"B.9-report"}, "B.9"),
        ("P1", {"P1-thing"}, set(), "P1"),
        # The boundary rules hold in the weaker tier too.
        ("foo-baz", set(), {"foo-bar"}, "foo-baz"),
        ("B.90-other", set(), {"B.9"}, "B.90-other"),
        ("P1-thing", set(), set(), "P1-thing"),
    ],
)
def test_component_of_falls_back_to_the_implied_vocabulary(name, ids, implied, expected):
    assert ts.component_of(name, ids, implied) == expected


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


def test_a_partly_written_map_resolves_the_components_it_does_not_name(project, capsys):
    """A map naming some components and not others is the normal state of a board.

    The vocabulary is chosen per name rather than all-or-nothing: `B.9` is not in the
    map, so it falls through to the ticket directory names, which name an id by
    construction. Taking the map's presence as proof that it is complete left every
    component it had not reached yet comparing raw names -- the whole defect, still
    open for exactly the specs a migration has not got to.
    """
    root = project(
        {"P1": [{}], "B.9": [{}]},
        specs=("P1-thing", "B.9-report"),
        map_rows=["| P1 | a thing | — |"],
    )
    assert status(root) == 0
    assert "no tickets cut" not in capsys.readouterr().err


def test_a_bare_spec_directory_does_not_reach_a_slugged_ticket_directory(project, capsys):
    """Resolution runs one way: a name carries an id, it never elaborates into one.

    So the reverse spelling -- bare spec directory, slugged ticket directory -- pairs
    only once the map declares the id, which the next test shows. Matching in reverse
    would close this case and cost more than it pays: with specs `foo-bar` and
    `foo-bar-baz` and tickets under the longer one, it credits `foo-bar` with its
    sibling's tickets and drops a true line. The remedy is declaration, not a wider
    guess; `templates/profile.md` says so where the ambiguity is born.
    """
    root = project({"P1-thing": [{}]}, specs=("P1",), map_rows=[])
    assert status(root) == 1
    assert "P1: spec written, no tickets cut" in capsys.readouterr().err


def test_declaring_the_id_resolves_the_reverse_spelling(project, capsys):
    """The remedy for either name form, and the reason the map is the authority."""
    root = project({"P1-thing": [{}]}, specs=("P1",), map_rows=["| P1 | a thing | — |"])
    assert status(root) == 0
    assert "no tickets cut" not in capsys.readouterr().err


def test_a_sibling_slug_keeps_its_line_when_the_tickets_are_under_the_longer_name(project, capsys):
    """The case that forbids reverse matching, without a map to lean on.

    `foo-bar` has no tickets of its own and must say so. This is the line reverse
    resolution would have swallowed, which is why it stays one-way.
    """
    root = project({"foo-bar-baz": [{}]}, specs=("foo-bar", "foo-bar-baz"), map_rows=[])
    assert status(root) == 1
    assert "foo-bar: spec written, no tickets cut" in capsys.readouterr().err


def test_without_a_map_a_sibling_slug_is_absorbed(project, capsys):
    """The price of the implied vocabulary, paid knowingly and pinned here.

    With no map, `foo-bar` is an id by construction and `foo-bar-baz` reads as a longer
    spelling of it, so a spec with no tickets of its own goes unreported. Nothing in
    the tree distinguishes the two readings -- only the ID column can, and
    `test_a_longer_slug_is_not_credited_with_a_shorter_one_s_tickets` is this same tree
    with a map. A test says so out loud, because the alternative is discovering the
    trade by accident and closing it with the worse one.
    """
    root = project({"foo-bar": [{}]}, specs=("foo-bar", "foo-bar-baz"), map_rows=[])
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


# --- Regressions found by a code review of a downstream repo, 2026-10-13 -------------


def _mk(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _ticket(num, title, blocked_by=None):
    return (
        f"# {num} — {title}\n\n"
        "**What becomes true:** something.\n\n"
        f"**Blocked by:** {blocked_by or 'none (can start immediately)'}\n"
        "**check_type:** manual\n"
        "**check:** look at it\n"
        "**Claimed by:** unclaimed\n\n"
        "## Outcome\n\n**PR:**\n**Diverged:**\n"
    )


def _profile(root):
    return _mk(
        root,
        "planning/agent/profile.md",
        "- **spec_dir:** planning/specs/\n"
        "- **ticket_dir:** `planning/tickets/<spec-id>/`\n"
        "- **spec_map_path:** planning/spec-map.md\n",
    )


def _map(root, ids):
    rows = "\n".join(f"| {i} | build | thing | — | — |" for i in ids)
    return _mk(
        root,
        "planning/spec-map.md",
        "# Spec map\n\n## Components\n\n| ID | Kind | Covers | Blocked by | Requires |\n"
        "|---|---|---|---|---|\n" + rows + "\n",
    )


def _run(root):
    import subprocess
    import sys

    here = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(here / "tools" / "ticket_status.py"),
            "--root",
            str(root),
            "--profile",
            str(root / "planning/agent/profile.md"),
            "--no-run",
        ],
        capture_output=True,
        text=True,
    )
    return r.stdout + r.stderr


def test_a_cross_spec_blocked_by_edge_resolves_against_the_spec_it_names(tmp_path):
    """`S2/05 blocked by S1/01` must look up S1/01, not S2/01.

    The prefix was discarded and replaced with the blocking ticket's OWN spec_id, so a
    valid cross-spec edge reported as dangling -- and worse, when a same-numbered ticket
    happened to exist under the citing spec, a genuinely dangling edge passed silently.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    _mk(tmp_path, "planning/specs/S2-b/spec.md", "# S2\n")
    _mk(tmp_path, "planning/tickets/S1/01-first.md", _ticket("01", "First"))
    _mk(tmp_path, "planning/tickets/S2/05-needs-s1.md", _ticket("05", "Needs S1", "S1/01"))
    out = _run(tmp_path)
    assert "blocked by 'S1/01', which does not exist" not in out, out


def test_a_dangling_cross_spec_edge_is_still_reported(tmp_path):
    """The mirror: the fix must not make every cross-spec edge pass."""
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    _mk(tmp_path, "planning/specs/S2-b/spec.md", "# S2\n")
    _mk(tmp_path, "planning/tickets/S1/01-first.md", _ticket("01", "First"))
    _mk(tmp_path, "planning/tickets/S2/05-needs.md", _ticket("05", "Needs", "S1/99"))
    assert "blocked by 'S1/99', which does not exist" in _run(tmp_path)


def test_an_unpadded_ticket_heading_does_not_dangle_every_edge_into_it(tmp_path):
    """`.zfill(2)` was applied to the blocked_by side only.

    A ticket headed `# 1 —` registers as `S1/1` while an edge naming it builds `S1/01`,
    so the board reports drift for a ticket set that is entirely well-formed. The
    template writes both as `NN` without saying the heading must be zero-padded.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    _mk(tmp_path, "planning/tickets/S1/01-first.md", _ticket("1", "First"))
    _mk(tmp_path, "planning/tickets/S1/02-second.md", _ticket("2", "Second", "1"))
    out = _run(tmp_path)
    assert "which does not exist" not in out, out


def test_an_empty_spec_directory_does_not_clear_the_planned_no_spec_line(tmp_path):
    """`mkdir` must not turn off the drift line the spec map exists to produce.

    `written` counted any directory under the spec root with no `spec.md` requirement,
    so an empty directory read as a written spec. The ticket side guards the symmetric
    case explicitly ("an empty directory must still read as 'no tickets cut'").
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    (tmp_path / "planning/specs/S2-empty").mkdir(parents=True)
    out = _run(tmp_path)
    assert "S2: planned in the spec map, no spec written" in out, out


def test_norm_number_treats_001_and_1_as_the_same_ticket():
    """`zfill` pads but never truncates, so `001` stayed `001` while `1` became `01`.

    The docstring claimed all three spellings were one ticket; they were two. A ticket
    file `001-slug.md` headed `# 001 -` would therefore dangle every edge naming `1`.
    """
    from ticket_status import norm_number

    assert norm_number("1") == norm_number("01") == norm_number("001") == "01"
    assert norm_number("010") == norm_number("10") == "10"
    assert norm_number("x") == "x"
    assert norm_number("1.5") == "1.5"


def test_edge_key_tolerates_surrounding_whitespace_on_both_sides():
    """The number side was stripped by `norm_number`; the spec side was not."""
    from ticket_status import edge_key

    assert edge_key("  S1/01  ", "S2") == "S1/01"
    assert edge_key(" 01 ", "S2") == "S2/01"


def test_a_cross_spec_edge_resolves_when_ticket_dirs_carry_the_full_slug(tmp_path):
    """The half the earlier `blocked_by` fix did not reach.

    `known` was keyed by raw TICKET DIRECTORY NAME while `edge_key` returned whatever
    the author typed, so the two sides of the comparison were spelled in different
    vocabularies. A repo whose ticket directories carry the full slug registers
    `S1-alpha/01`, an edge naming the declared id builds `S1/01`, and a valid edge
    reported as dangling against a ticket sitting right there.

    The test above this one passes only because it names its ticket directories `S1/`
    and `S2/` -- the one spelling where raw comparison happens to work. A check written
    with the spelling that works is not a check.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-alpha/spec.md", "# S1\n")
    _mk(tmp_path, "planning/specs/S2-beta/spec.md", "# S2\n")
    _mk(tmp_path, "planning/tickets/S1-alpha/01-first.md", _ticket("01", "First"))
    _mk(tmp_path, "planning/tickets/S2-beta/01-second.md", _ticket("01", "Second", "S1/01"))
    out = _run(tmp_path)
    assert "which does not exist" not in out, out


def test_a_dangling_edge_still_dangles_when_ticket_dirs_carry_the_full_slug(tmp_path):
    """The mirror of the fix above: resolving through the vocabulary must not
    make every cross-spec edge pass. `S1/99` does not exist in any spelling."""
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-alpha/spec.md", "# S1\n")
    _mk(tmp_path, "planning/specs/S2-beta/spec.md", "# S2\n")
    _mk(tmp_path, "planning/tickets/S1-alpha/01-first.md", _ticket("01", "First"))
    _mk(tmp_path, "planning/tickets/S2-beta/01-second.md", _ticket("01", "Second", "S1/99"))
    assert "blocked by 'S1/99', which does not exist" in _run(tmp_path)


def test_a_spec_directory_holding_only_litter_is_not_a_written_spec(tmp_path):
    """`any(p.iterdir())` was satisfied by anything at all.

    So `mkdir planning/specs/S2-x/.ipynb_checkpoints` turned off the "planned, no spec
    written" line without a spec existing -- the same defect the empty-directory fix
    addressed, one layer down, and reachable by a tool the author never ran deliberately.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    _mk(tmp_path, "planning/specs/S2-x/.ipynb_checkpoints/spec-checkpoint.md", "junk\n")
    out = _run(tmp_path)
    assert "S2: planned in the spec map, no spec written" in out, out
    assert "S2-x: spec written, no tickets cut" not in out, out


def test_a_dotfile_alone_is_not_a_written_spec_either(tmp_path):
    """The macOS half of the same hole: `.DS_Store` appears without anyone authoring it."""
    _profile(tmp_path)
    _map(tmp_path, ["S1"])
    _mk(tmp_path, "planning/specs/S1-a/.DS_Store", "\0\0")
    assert "S1: planned in the spec map, no spec written" in _run(tmp_path)


def test_a_spec_file_not_named_spec_md_still_counts_as_written(tmp_path):
    """The guard above must not tighten into "a file called spec.md".

    The spec path pattern is a profile key and a repo may name the file anything; the
    condition is that a human wrote SOMETHING there.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1"])
    _mk(tmp_path, "planning/specs/S1-a/agreement.md", "# S1\n")
    assert "S1: planned in the spec map, no spec written" not in _run(tmp_path)


def test_the_spec_map_reads_only_its_component_table(tmp_path):
    """Every 3+ column row in the file was a component, header rows included.

    A map carrying a second table -- "Vocabulary gaps", "Needs not yet covered", any
    table at all -- reported one phantom planned component per row plus its header, as
    drift lines naming things nobody planned. The report's whole value is being
    trustworthy when it is red.
    """
    path = tmp_path / "spec-map.md"
    path.write_text(
        "| ID | Kind | Covers |\n"
        "|---|---|---|\n"
        "| S1 | build | loader |\n"
        "\n"
        "## Vocabulary gaps\n"
        "\n"
        "| Term | Why it is unsettled | Owner |\n"
        "|---|---|---|\n"
        "| sponsor | two meanings in one document | Dana Reed |\n"
        "| intake | ambiguous between the two | Morgan Vale |\n"
    )
    assert ts.parse_spec_map(path) == ["S1"]


def test_a_map_whose_id_column_is_headed_differently_still_parses(tmp_path):
    """Reading one table too few is as wrong as reading one too many, and quieter.

    Scoping to a literal `ID` header alone would parse a `Component`-headed map to zero
    ids, and the "planned, no spec written" condition would stop firing in silence.
    """
    path = tmp_path / "spec-map.md"
    path.write_text(
        "| Component | Kind | Covers |\n"
        "|---|---|---|\n"
        "| S1 | build | loader |\n"
        "| S2 | experiment | comparison |\n"
    )
    assert ts.parse_spec_map(path) == ["S1", "S2"]


def test_the_id_table_wins_wherever_it_sits_in_the_file(tmp_path):
    """The fallback must not beat an explicit ID header that comes later."""
    path = tmp_path / "spec-map.md"
    path.write_text(
        "| Term | Why | Owner |\n|---|---|---|\n| sponsor | unsettled | Dana Reed |\n"
        "\n"
        "| ID | Kind | Covers |\n|---|---|---|\n| S1 | build | loader |\n"
    )
    assert ts.parse_spec_map(path) == ["S1"]


def test_a_fenced_example_table_is_documentation_not_the_component_list(tmp_path):
    """The regression that turned the board GREEN WITH EXIT 0.

    A map that shows its own row format in a ``` fence: the fence's table was the first
    `ID`-headed one, so positional scoping picked it, its single row read `| S<n> | ... |`
    which `_MAP_ROW` rejects, and the winning table was EMPTY. Zero components planned,
    no drift, exit 0 -- a drift detector going silent, which is the worst outcome it has.

    `deconstruct/references/spec-map-skeleton.md` is itself a fenced spec map, so this is
    a shape a repo is likely to copy.
    """
    path = tmp_path / "spec-map.md"
    # The example rows carry REAL-SHAPED ids, which is what the shipped skeleton does --
    # `F1`, `F2`, `B1`. A first version of this test used `S<n>`, which `_MAP_ROW` rejects
    # anyway, so it passed with fence-skipping disabled: the union fix alone was carrying
    # it. Mutation-testing caught the test passing for the wrong reason.
    path.write_text(
        "A row looks like this:\n\n"
        "```\n"
        "| ID | Kind | Covers |\n|---|---|---|\n"
        "| F1 | build | the need, one line |\n| F2 | knowledge-revision | ... |\n"
        "```\n\n"
        "## Components\n\n"
        "| ID | Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n| S2 | build | two |\n"
    )
    assert ts.parse_spec_map(path) == ["S1", "S2"], (
        "a fenced example is documentation; its rows are not planned components"
    )


def test_a_header_carrying_markup_or_a_space_still_names_the_id_column(tmp_path):
    """A header is not a row and does not obey a row's content rules.

    `_MAP_ROW` requires a first cell of alphanumerics, dots and dashes, so `Spec ID` and
    `**ID**` failed it -- the header line was skipped entirely, the SEPARATOR row became
    the table's "header" flagged not-ID, and with another table ahead of it the wrong
    table won: real ids vanished AND foreign ids were minted as planned components.
    """
    for head in ("| ID |", "| **ID** |", "| Spec ID |", "| `id` |", "| ID# |"):
        path = tmp_path / "m.md"
        path.write_text(
            "## Vocabulary gaps\n\n"
            "| Term | Why | Owner |\n|---|---|---|\n| sponsor | unsettled | Dana Reed |\n\n"
            "## Components\n\n"
            f"{head} Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n"
        )
        assert ts.parse_spec_map(path) == ["S1"], f"header {head!r} lost the real component"


def test_a_component_list_split_over_two_id_tables_keeps_both(tmp_path):
    """Positional scoping returned on the first match and dropped the rest."""
    path = tmp_path / "m.md"
    path.write_text(
        "| ID | Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n\n"
        "| ID | Kind | Covers |\n|---|---|---|\n| S2 | build | two |\n| S3 | build | three |\n"
    )
    assert ts.parse_spec_map(path) == ["S1", "S2", "S3"]


def test_an_unrecognised_header_falls_back_to_every_table_never_to_nothing(tmp_path):
    """Rule 1: never lose a real id.

    A phantom component is a loud extra line. A LOST component silently stops producing
    the "planned, no spec written" condition for something real. So where no header names
    an ID column, the fallback is the union of every table -- never narrower than reading
    the whole file was, which is what the first attempt at scoping got backwards.
    """
    path = tmp_path / "m.md"
    path.write_text(
        "| Component | Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n\n"
        "| Thing | Kind | Covers |\n|---|---|---|\n| S2 | build | two |\n"
    )
    assert ts.parse_spec_map(path) == ["S1", "S2"]


def test_an_empty_file_is_not_a_written_spec(tmp_path):
    """`touch spec.md` turned off the "planned, no spec written" line.

    The third layer of the same hole, and the only one that happens BY ACCIDENT: a
    scaffolding step or an interrupted write leaves exactly a 0-byte `spec.md`.
    """
    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    (tmp_path / "planning/specs/S2-b").mkdir(parents=True)
    (tmp_path / "planning/specs/S2-b/spec.md").write_text("")
    out = _run(tmp_path)
    assert "S2: planned in the spec map, no spec written" in out, out


def test_an_unreadable_spec_directory_does_not_crash_the_board(tmp_path):
    """A traceback in a drift detector loses the other fifteen lines along with this one."""
    import os
    import stat

    _profile(tmp_path)
    _map(tmp_path, ["S1", "S2"])
    _mk(tmp_path, "planning/specs/S1-a/spec.md", "# S1\n")
    blocked = tmp_path / "planning/specs/S2-b"
    blocked.mkdir(parents=True)
    (blocked / "spec.md").write_text("# S2\n")
    os.chmod(blocked, 0)
    try:
        out = _run(tmp_path)
        assert "Traceback" not in out, out
        assert "S2: planned in the spec map, no spec written" in out, out
    finally:
        os.chmod(blocked, stat.S_IRWXU)


def test_a_non_decimal_unicode_digit_does_not_crash_norm_number():
    """`isdigit()` is True for category-No characters that `int()` rejects.

    A superscript two in a ticket heading or a `Blocked by:` value raised ValueError and
    took the whole board down. Both are author-typed text.
    """
    from ticket_status import norm_number

    assert norm_number("²") == "²"
    assert norm_number("⅕") == "⅕"
    assert norm_number("7") == "07"


def test_an_unclosed_fence_does_not_swallow_the_rest_of_the_map(tmp_path):
    """The exit-0 path, reopened by my own fence fix and closed again.

    `fenced = not fenced` is a plain toggle, so ONE dropped closing fence made every
    later line fenced: a map whose Components table sat below an unterminated ``` block
    parsed to zero ids, and the board printed "no drift" with exit 0. Same class as the
    fenced-example defect, reached from a single missing backtick in a hand-edited file.

    An unmatched trailing fence is ignored rather than opening a region to EOF, because
    rule 1 -- never lose a real id -- has to hold for malformed markdown too.
    """
    path = tmp_path / "spec-map.md"
    path.write_text(
        "```python\n"
        'print("how a row is written")\n'
        "\n"
        "## Components\n\n"
        "| ID | Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n| S2 | build | two |\n"
    )
    assert ts.parse_spec_map(path) == ["S1", "S2"]


def test_a_closed_fence_still_hides_its_rows_when_more_fences_follow(tmp_path):
    """The mirror: ignoring UNCLOSED fences must not stop CLOSED ones working, and a
    second, properly closed fence later in the file must not re-pair the first one."""
    path = tmp_path / "spec-map.md"
    path.write_text(
        "```\n| ID | Kind | Covers |\n|---|---|---|\n| F1 | build | example |\n```\n\n"
        "## Components\n\n"
        "| ID | Kind | Covers |\n|---|---|---|\n| S1 | build | one |\n\n"
        "```\n| ID | Kind | Covers |\n|---|---|---|\n| F2 | build | another |\n```\n"
    )
    assert ts.parse_spec_map(path) == ["S1"]
