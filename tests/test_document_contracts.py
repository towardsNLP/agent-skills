"""Regression checks for contracts shared across skill documents."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_GROUPS = ("session", "sdd", "thinking", "knowledge", "craft")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def skill_manifests() -> list[Path]:
    return sorted(
        manifest for group in SKILL_GROUPS for manifest in (ROOT / group).rglob("SKILL.md")
    )


def test_check_contracts_uses_profile_key_names():
    profile = read("templates/profile.md")
    keys = set(re.findall(r"^- \*\*([a-z_]+):\*\*", profile, re.MULTILINE))
    skill = read("sdd/check-contracts/SKILL.md")

    for key in (
        "doc_precedence_order",
        "authority_map",
        "constraints_doc",
        "spec_path_pattern",
        "workstream_id_scheme",
        "branch_convention",
        "gated_changes",
        "forbidden_terms",
        "write_scope",
    ):
        assert key in keys
        assert f"`{key}`" in skill

    assert "contract_sources" not in skill
    assert "branch_naming" not in skill


def test_a_skill_that_names_the_default_spec_path_also_names_the_key():
    """`spec_path_pattern` is a declared profile key, so no skill may assume its default.

    `templates/profile.md` offers `planning/specs/<spec-id>/spec.md` as one project's
    answer, and the key exists so a project can declare another. A project whose pattern
    carries a slug got its spec written to a second tree that matched neither the profile
    nor its own decision record, while `tools/ticket_status.py` had already been built to
    accept slug-named spec directories (`component_of` resolves them against the map's ID
    column). So the tool honoured the choice and three skills did not.

    The path may still appear as the counterexample it is. What it may not do is appear
    without the key that overrides it.
    """
    for manifest in skill_manifests():
        body = manifest.read_text(encoding="utf-8")
        if "spec_dir/<spec-id>/" not in body:
            continue
        assert "spec_path_pattern" in body, (
            f"{manifest.relative_to(ROOT)} names the default spec path "
            "`spec_dir/<spec-id>/...` without naming `spec_path_pattern`. State the key that "
            "decides the path, or do not state a path."
        )


def test_effective_agreement_is_visible_to_ticketing_and_implementation():
    assert "amendments.md" in read("sdd/tickets/SKILL.md")
    assert "amendments.md" in read("sdd/implement/SKILL.md")


def test_spec_map_has_one_writer_and_no_status_cache():
    adr_spec = read("sdd/adr-spec/SKILL.md")
    assert "Do not add a link or status to `spec_map_path`" in adr_spec
    assert "`/sync-progress` is its only writer" in adr_spec


def test_ticket_template_does_not_ship_a_pr_placeholder():
    template = read("sdd/tickets/references/ticket-template.md")
    assert "**PR:**\n" in template
    assert "**PR:** #NN" not in template


def test_start_session_reads_the_real_freshness_fields():
    skill = read("session/start-session/SKILL.md")
    helper = read("session/start-session/scripts/context_packet.py")
    assert "state_as_of" in helper
    assert "_DATE_HEADING" in helper
    assert "grep -m1 -h '^## 20'" not in skill


def test_profile_separates_personal_state_from_shared_index():
    profile = read("templates/profile.md")
    assert "**state_dir:**" in profile
    assert "**shared_state_path:**" in profile
    assert "**state_path:**" not in profile


def test_portable_skills_do_not_name_the_claude_skill_tool_or_transcript_path():
    skill_text = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.rglob("SKILL.md"))
    assert "Skill tool" not in skill_text
    assert "~/.claude/projects/" not in skill_text


def test_openai_sidecars_cover_every_skill_and_match_invocation_policy():
    manifests = skill_manifests()
    expected_sidecars = {manifest.parent / "agents/openai.yaml" for manifest in manifests}
    actual_sidecars = {
        sidecar for group in SKILL_GROUPS for sidecar in (ROOT / group).rglob("agents/openai.yaml")
    }

    assert actual_sidecars == expected_sidecars
    for manifest in manifests:
        frontmatter = manifest.read_text(encoding="utf-8").split("---", 2)[1]
        sidecar = manifest.parent / "agents/openai.yaml"
        metadata = sidecar.read_text(encoding="utf-8")

        display_name = re.search(r'^  display_name: "([^"]+)"$', metadata, re.MULTILINE)
        short_description = re.search(r'^  short_description: "([^"]+)"$', metadata, re.MULTILINE)
        implicit = re.search(r"^  allow_implicit_invocation: (true|false)$", metadata, re.MULTILINE)

        assert display_name, sidecar
        assert short_description, sidecar
        assert 25 <= len(short_description.group(1)) <= 64, sidecar
        assert implicit, sidecar
        assert (implicit.group(1) == "true") == (
            "disable-model-invocation: true" not in frontmatter
        ), sidecar
        assert "model:" not in metadata


def test_tdd_contains_the_refactor_phase():
    skill = read("craft/tdd/SKILL.md")
    assert "Refactor while green" in skill
    assert "Refactoring is not part of the loop" not in skill


def test_linker_never_recursively_deletes_an_install_target():
    assert "rm -rf" not in read("bin/link.sh")
