"""The startup packet stays small, selective and host-neutral."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "session/start-session/scripts/context_packet.py"


def load_module():
    spec = importlib.util.spec_from_file_location("start_context_packet", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


context_packet = load_module()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def project(
    tmp_path: Path, *, state_date: str = "2026-09-24", claimant: str = "Ahmad Hashemi"
) -> Path:
    write(
        tmp_path / "planning/agent/profile.md",
        """# Agent profile

## Identity and people
- **contributors:**
  - Ahmad Hashemi — lead, active

## Diaries
- **diary_dir:** `planning/diaries/`
- **diary_filename:** `<first>-diary.md`
- **state_dir:** `planning/agent/state/`

## Specs, tickets and decisions
- **ticket_dir:** `planning/tickets/<spec-id>/`

## Git
- **branch_convention:** `<owner>-<topic>-<number>`
""",
    )
    write(
        tmp_path / "planning/agent/state/ahmad.md",
        f"""# State

**state_as_of:** {state_date}

## Now

- **Branch:** `main`
- **Phase / workstream:** P2.3 — ontology revision
- **Work kind:** knowledge-revision
- **Ticket:** `planning/tickets/P2.3-ontology/03-revise-authority.md`
- **Governing spec:** `planning/specs/P2.3-ontology/spec.md`
- **Question:** Which authority governs conflicting jurisdiction labels?
- **Evidence context:** ontology v7; source registry 2026-09-20
- **Last verified:** `make validate-ontology`
- **Next action:** revise the authority relation after confirming ticket 03

## Recent

- THIS RECENT HISTORY MUST NOT ENTER THE PACKET

## Open

- THIS UNRELATED GLOBAL RISK MUST NOT ENTER THE PACKET
""",
    )
    write(
        tmp_path / "planning/tickets/P2.3-ontology/03-revise-authority.md",
        f"""# 03 — Revise authority

**What becomes true:** Conflicting jurisdiction labels resolve through one explicit
authority relation without copying the source hierarchy.
**Blocked by:** none (can start immediately)
**Governs:** `spec.md#3-scope`; `ontology.ttl#Authority`; ADR-0007
**check_type:** query
**check:** `python tools/check_competency.py CQ-14`
**Claimed by:** {claimant}

## Approach (non-binding, ≤150 words)

THIS LONG APPROACH MUST NOT ENTER THE PACKET.

## Outcome

THIS OUTCOME MUST NOT ENTER THE PACKET.
""",
    )
    write(tmp_path / "planning/diaries/ahmad-diary.md", "# Diary\n\n## 2026-09-24 — Work\n")
    write(
        tmp_path / "planning/specs/P2.3-ontology/spec.md",
        "THIS FULL SPEC MUST NEVER ENTER THE STARTUP PACKET\n" * 100,
    )
    return tmp_path


def test_packet_reads_only_routing_fields(tmp_path: Path, monkeypatch) -> None:
    root = project(tmp_path)
    original_read = context_packet.read_text
    reads: list[Path] = []

    def tracked_read(path: Path) -> str:
        reads.append(path)
        return original_read(path)

    monkeypatch.setattr(context_packet, "read_text", tracked_read)
    output = context_packet.build_packet(
        root,
        contributor="Ahmad Hashemi",
        branch="main",
    )

    assert len(output) <= context_packet.DEFAULT_MAX_CHARS
    assert len(output.split()) <= 250
    assert "Conflicting jurisdiction labels" in output
    assert "without copying the source hierarchy" in output
    assert "spec.md#3-scope" in output
    assert "check_competency.py CQ-14" in output
    assert "THIS RECENT HISTORY" not in output
    assert "THIS UNRELATED GLOBAL RISK" not in output
    assert "THIS LONG APPROACH" not in output
    assert "THIS FULL SPEC" not in output
    assert "create a topic branch" in output
    assert not any(path.name == "spec.md" for path in reads)


def test_packet_flags_stale_state_and_foreign_claim(tmp_path: Path) -> None:
    root = project(tmp_path, state_date="2026-09-20", claimant="Morgan Vale")
    output = context_packet.build_packet(
        root,
        contributor="Ahmad Hashemi",
        branch="ahmad-ontology-31",
    )

    assert "State is stale" in output
    assert "claimed by Morgan Vale" in output
    assert "differs from recorded branch" in output


def test_packet_fails_closed_when_budget_is_exceeded(tmp_path: Path) -> None:
    root = project(tmp_path)
    output = context_packet.build_packet(
        root,
        contributor="Ahmad Hashemi",
        branch="main",
        max_chars=800,
    )

    assert len(output) <= 800
    assert "blocked" in output
    assert "no field was clipped" in output
    assert "do not load broad documents" in output
    assert "…" not in output


def test_long_field_is_kept_whole_when_the_complete_card_fits(tmp_path: Path) -> None:
    root = project(tmp_path)
    ticket = root / "planning/tickets/P2.3-ontology/03-revise-authority.md"
    marker = "END-OF-COMPLETE-GOAL"
    long_goal = " ".join(["meaningful"] * 35) + f" {marker}"
    text = ticket.read_text(encoding="utf-8")
    text = text.replace(
        "Conflicting jurisdiction labels resolve through one explicit\n"
        "authority relation without copying the source hierarchy.",
        long_goal,
    )
    ticket.write_text(text, encoding="utf-8")

    output = context_packet.build_packet(
        root,
        contributor="Ahmad Hashemi",
        branch="ahmad-ontology-31",
    )

    assert len(long_goal) > context_packet.LONG_FIELD_CHARS
    assert long_goal in output
    assert marker in output
    assert "[open source]" not in output


def test_overflow_never_returns_a_prefix_of_an_acceptance_command(tmp_path: Path) -> None:
    root = project(tmp_path)
    ticket = root / "planning/tickets/P2.3-ontology/03-revise-authority.md"
    command = "python tools/check_competency.py " + "CQ-14-" * 120 + "COMMAND-END"
    text = ticket.read_text(encoding="utf-8")
    text = text.replace("python tools/check_competency.py CQ-14", command)
    ticket.write_text(text, encoding="utf-8")

    output = context_packet.build_packet(
        root,
        contributor="Ahmad Hashemi",
        branch="ahmad-ontology-31",
        max_chars=800,
    )

    assert len(output) <= 800
    assert "blocked" in output
    assert command not in output
    assert command[:80] not in output
    assert "COMMAND-END" not in output


def test_a_task_outside_the_project_is_refused_rather_than_read(tmp_path: Path) -> None:
    """An escaping path has no project-relative rendering, and reading it widens the boundary."""
    root = project(tmp_path / "repo")
    outside = tmp_path / "elsewhere/01-secret.md"
    write(outside, "# 01 — Secret\n\n**What becomes true:** LEAKED-FROM-OUTSIDE\n")

    for task in (str(outside), "../elsewhere/01-secret.md"):
        output = context_packet.build_packet(
            root, task=task, contributor="Ahmad Hashemi", branch="ahmad-ontology-31"
        )
        assert "LEAKED-FROM-OUTSIDE" not in output
        assert "No ticket inside the project resolves" in output


def test_a_symlinked_escape_is_refused_too(tmp_path: Path) -> None:
    root = project(tmp_path / "repo")
    outside = tmp_path / "elsewhere/01-secret.md"
    write(outside, "# 01 — Secret\n\n**What becomes true:** LEAKED-VIA-SYMLINK\n")
    link = root / "planning/tickets/P2.3-ontology/09-link.md"
    link.symlink_to(outside)

    output = context_packet.build_packet(
        root,
        task="planning/tickets/P2.3-ontology/09-link.md",
        contributor="Ahmad Hashemi",
        branch="ahmad-ontology-31",
    )

    assert "LEAKED-VIA-SYMLINK" not in output
    assert "No ticket inside the project resolves" in output


def test_blocked_card_keeps_the_conflict_warnings(tmp_path: Path) -> None:
    """A foreign claim is what should stop the session, so overflow must not drop it."""
    root = project(tmp_path, claimant="Morgan Vale")
    ticket = root / "planning/tickets/P2.3-ontology/03-revise-authority.md"
    goal = " ".join(["meaningful"] * 400)
    ticket.write_text(
        ticket.read_text(encoding="utf-8").replace(
            "Conflicting jurisdiction labels resolve through one explicit\n"
            "authority relation without copying the source hierarchy.",
            goal,
        ),
        encoding="utf-8",
    )

    output = context_packet.build_packet(
        root, contributor="Ahmad Hashemi", branch="main", max_chars=800
    )

    assert "blocked" in output
    assert goal not in output
    assert "claimed by Morgan Vale" in output
    assert "trunk branch" in output


def test_freshness_is_not_claimed_without_a_diary_to_compare(tmp_path: Path) -> None:
    root = project(tmp_path)
    (root / "planning/diaries/ahmad-diary.md").unlink()

    output = context_packet.build_packet(
        root, contributor="Ahmad Hashemi", branch="ahmad-ontology-31"
    )

    assert "State freshness" not in output
    assert "No diary entry to compare against" in output


def test_a_budget_too_small_for_the_blocked_card_is_refused(tmp_path: Path) -> None:
    """Below the floor even the fixed refusal overflows, so the ceiling cannot be honoured."""
    with pytest.raises(ValueError):
        context_packet.build_packet(project(tmp_path), max_chars=context_packet.MIN_MAX_CHARS - 1)


def test_a_name_that_is_only_a_substring_is_not_on_the_roster(tmp_path: Path) -> None:
    """A roster listing Ahmad Hashemi does not make "Ahma" a contributor."""
    root = project(tmp_path)

    assert "roster" not in context_packet.build_packet(root, contributor="Ahmad Hashemi")
    assert "not present in the profile contributor roster" in context_packet.build_packet(
        root, contributor="Ahma"
    )


def test_skill_is_model_neutral_and_runs_the_script_without_delegating() -> None:
    skill = (ROOT / "session/start-session/SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---", 2)[1]

    assert "model:" not in frontmatter
    assert "agent:" not in frontmatter
    assert "context: fork" in frontmatter
    assert "background: false" in frontmatter
    assert "scripts/context_packet.py" in skill
    assert "Do not open the profile" in skill
    # The script bounds its own output, so a relayed worker adds a failure path
    # without narrowing what reaches the model. Both stay refused by name.
    assert "Do not delegate this command" in skill
    assert "isolated worker, subagent or fork" in skill
    assert "vendor-specific agent type" in skill
