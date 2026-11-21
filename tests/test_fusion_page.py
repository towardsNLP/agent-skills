"""A fusion page's anatomy and its two templates must not drift apart.

`references/anatomy.md` names each section of a fusion page by id and by heading. A page is
started from `references/page.html` or `references/page.md`, so a section the anatomy names but a
template lacks is a section the skill tells the agent to fill and the agent never sees.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "thinking" / "fusion"
REFS = SKILL / "references"


def read(name: str) -> str:
    return (REFS / name).read_text(encoding="utf-8")


def sections() -> list[tuple[str, str]]:
    """(id, heading) for every row of the anatomy's section table."""
    return [
        (section_id, heading.strip())
        for section_id, heading in re.findall(
            r"^\| `([a-z-]+)` \| ([^|]+) \|", read("anatomy.md"), re.M
        )
    ]


def test_the_anatomy_names_its_sections():
    ids = [section_id for section_id, _ in sections()]
    assert len(ids) >= 10, ids
    assert len(ids) == len(set(ids)), ids
    assert {"ledger", "frame", "edge", "forks", "contributions"} <= set(ids)


def test_the_html_template_carries_every_section():
    html = read("page.html")
    missing = [section_id for section_id, _ in sections() if f'id="{section_id}"' not in html]
    assert not missing, f"page.html lacks the sections anatomy.md names: {missing}"


def test_the_markdown_shape_carries_every_section():
    headings = set(re.findall(r"^#{2,3} (.+)$", read("page.md"), re.M))
    missing = [heading for _, heading in sections() if heading not in headings]
    assert not missing, f"page.md lacks the headings anatomy.md names: {missing}"


def test_the_provisional_recommendation_is_folded_in_both_templates():
    """The recommendation's reasoning stays folded, with what would change the agent's mind."""
    for name in ("page.html", "page.md"):
        text = read(name)
        assert re.search(
            r"<details>\s*<summary>Show my provisional recommendation</summary>", text
        ), name
        assert "What would change my mind" in text, name


def test_the_skill_points_at_every_reference_and_every_pointer_resolves():
    pointed = set(
        re.findall(r"\(references/([\w.-]+)\)", (SKILL / "SKILL.md").read_text(encoding="utf-8"))
    )
    present = {path.name for path in REFS.iterdir() if path.is_file()}
    assert pointed == present, f"unreferenced: {present - pointed}; missing: {pointed - present}"


def fork_card_fields() -> list[str]:
    """Field names of the anatomy's fork card table, in order."""
    card = read("anatomy.md").split("## The fork card", 1)[1]
    return re.findall(r"^\| \*\*([^*]+)\*\* \|", card, re.M)


def test_both_templates_put_fork_card_fields_in_the_anatomy_order():
    """What is at stake comes before the options, and the lean comes after them."""
    fields = fork_card_fields()
    assert fields[:4] == ["Where", "Problem", "At stake", "Options"], fields
    for name in ("page.html", "page.md"):
        card = read(name).split("Forks", 1)[1]
        positions = [card.lower().find(field.lower()) for field in fields]
        assert -1 not in positions, (name, dict(zip(fields, positions)))
        assert positions == sorted(positions), (name, dict(zip(fields, positions)))


def test_both_templates_keep_the_anatomy_section_order():
    html = read("page.html")
    html_positions = [html.find(f'id="{section_id}"') for section_id, _ in sections()]
    assert html_positions == sorted(html_positions), "page.html section order differs"
    headings = re.findall(r"^## (.+)$", read("page.md"), re.M)
    wanted = [heading for _, heading in sections()]
    assert [h for h in headings if h in wanted] == wanted, "page.md section order differs"


def test_every_reader_of_a_finished_page_runs_the_same_resumption_check():
    """Three skills describe the check; each must keep its three moves."""
    for path in ("thinking/fusion/SKILL.md", "sdd/adr-spec/SKILL.md", "sdd/deconstruct/SKILL.md"):
        text = " ".join((ROOT / path).read_text(encoding="utf-8").split())
        assert "resumption check" in text, path
        for move in ("ledger", '"facts checked against"', "premise that changed", "still stand"):
            assert move in text, (path, move)


def test_every_html_question_preselects_exactly_one_recommendation():
    """The user starts from the recommendation and changes it in one click."""
    html = read("page.html")
    groups = re.findall(
        r'data-q="([A-Z]\d+)" data-kind="(fork|assumption|default)"(.*?)</div>', html, re.S
    )
    assert groups, "no answerable questions in page.html"
    for qid, _, body in groups:
        recommended = re.findall(r"<input [^>]*data-recommended[^>]*>", body)
        assert len(recommended) == 1 and "checked" in recommended[0], qid
        assert body.count(" checked") == 1, qid


def test_the_html_answers_can_be_gathered_and_copied():
    html = read("page.html")
    for control in ('id="fz-gather"', 'id="fz-copy"', 'id="fz-summary"', 'id="fz-responder"'):
        assert control in html, control
    assert "kept the recommendation" in html and "CHANGED from" in html
    assert "localStorage" in html and "execCommand" in html


def test_every_html_fork_block_names_its_kind_and_label():
    """The summary reports a question by id, kind and label, so each must carry all three."""
    for attrs in re.findall(r"<div class=\"q\"([^>]*)>", read("page.html")):
        assert re.search(r'data-q="[A-Z]\d+"', attrs), attrs
        assert re.search(r'data-kind="(fork|assumption|default|edge)"', attrs), attrs
        assert 'data-label="' in attrs, attrs


def test_the_answer_script_is_valid_javascript():
    """A syntax error silently disables the whole form, so check it where node exists."""
    import shutil
    import subprocess
    import tempfile

    node = shutil.which("node")
    if not node:
        import pytest

        pytest.skip("node is not installed")
    html = read("page.html")
    script = html[html.rindex("<script>") + len("<script>") : html.rindex("</script>")]
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(script)
    result = subprocess.run([node, "--check", handle.name], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
