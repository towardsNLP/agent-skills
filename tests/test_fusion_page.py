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
    adr_spec = " ".join((ROOT / "sdd/adr-spec/SKILL.md").read_text(encoding="utf-8").split())
    assert "A finished **review page**" in adr_spec, "/adr-spec must accept a finished review page"


def test_every_scale_in_the_skill_has_a_column_in_scales_md():
    """Step 1 names the scales; scales.md says what each section holds at each of them."""
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    step_one = skill.split("## Step 1", 1)[1].split("## Step 2", 1)[0]
    scales = re.findall(r"^\| \*\*([a-z ]+)\*\* \|", step_one, re.M)
    assert scales == ["project", "first component", "component", "review"], scales
    header = next(line for line in read("scales.md").splitlines() if line.startswith("| Section"))
    columns = [cell.split(":")[0].strip().lower() for cell in header.strip("|").split("|")[1:]]
    assert columns == scales, columns
    for name in ("page.html", "page.md"):
        masthead = re.search(r"[Ss]cale:\*?\*? ?[{<]([^}>]+)[}>]", read(name))
        assert masthead, name
        listed = [part.strip() for part in masthead.group(1).split("|")]
        assert listed == scales, (name, listed)


def test_the_closing_summary_is_written_from_the_log_not_asked():
    """The log already holds what the user contributed; asking them to restate it is busywork."""
    skill = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
    assert "do not ask the user to restate it" in skill
    assert "what did you contribute" not in skill.lower()
    for name in ("page.html", "page.md"):
        text = " ".join(read(name).split())
        assert "written from this log" in text, name
        assert "what did you contribute" not in text.lower(), name


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


def answer_script() -> str:
    html = read("page.html")
    return html[html.rindex("<script>") + len("<script>") : html.rindex("</script>")]


def node_or_skip() -> str:
    import shutil

    node = shutil.which("node")
    if not node:
        import pytest

        pytest.skip("node is not installed")
    return node


def test_the_answer_script_is_valid_javascript():
    """A syntax error silently disables the whole form, so check it where node exists."""
    import subprocess
    import tempfile

    node = node_or_skip()
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(answer_script())
    result = subprocess.run([node, "--check", handle.name], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


# A stand-in for the few DOM calls the answer script makes: forks with a recommendation, one
# default, the form's controls and a saved draft. Each case gathers the summary after its own
# clicks.
FORM_HARNESS = """
function page(forks = 1, saved = null) {
  const els = {}, listeners = {};
  for (const id of ["fz-responder", "fz-free", "fz-summary"]) els[id] = { value: "" };
  els["fz-status"] = { textContent: "" };
  for (const id of ["fz-gather", "fz-copy"]) els[id] = { addEventListener(t, f) { this.f = f; } };
  function block(q, kind, values) {
    const b = { dataset: { q, kind, label: q }, note: { value: "" } };
    // Checking one radio unchecks the rest of its group, as a browser does.
    b.radios = values.map((v, i) => {
      const r = { type: "radio", value: v, rec: i === 0, on: i === 0, closest: () => b };
      Object.defineProperty(r, "checked", { get: () => r.on,
        set: (x) => { if (x) b.radios.forEach((o) => { o.on = false; }); r.on = x; } });
      return r;
    });
    b.querySelector = (s) => s === "[data-note]" ? b.note
      : s === "input[data-recommended]" ? b.radios.find((r) => r.rec)
      : b.radios.find((r) => r.checked) || null;
    b.querySelectorAll = () => b.radios;
    return b;
  }
  const blocks = [];
  for (let i = 1; i <= forks; i++) blocks.push(block("F" + i, "fork", ["a", "b"]));
  blocks.push(block("D1", "default", ["keep", "veto"]));
  globalThis.document = { title: "T", getElementById: (id) => els[id] || null,
    querySelector: () => ({ textContent: "round 1" }), querySelectorAll: () => blocks,
    addEventListener: (t, f) => { (listeners[t] = listeners[t] || []).push(f); } };
  globalThis.localStorage = { getItem: () => saved && JSON.stringify(saved), setItem: () => {} };
  globalThis.navigator = {};
  globalThis.window = { isSecureContext: false };
  new Function(SCRIPT)();
  const fire = (t, target) => (listeners[t] || []).forEach((f) => f({ target }));
  const gather = () => { els["fz-gather"].f(); return els["fz-summary"].value; };
  return { els, blocks, fire, gather };
}
const out = {};
let p = page();
out.untouched = p.gather();
p = page(); p.els["fz-free"].value = "a reframe"; out.freeTextOnly = p.gather();
p = page(); p.fire("click", p.blocks[0].radios[0]); out.confirmed = p.gather();
p = page(); p.blocks[0].radios[0].checked = false; p.blocks[0].radios[1].checked = true;
p.fire("change", p.blocks[0].radios[1]); out.changedByKeyboard = p.gather();
p = page(2); p.fire("click", p.blocks[1].radios[0]); out.oneOfTwoClicked = p.gather();
p = page(1, { responder: "", free: "", q: { F1: { v: "b", n: "" } } });
out.oldDraftChanged = p.gather();
console.log(JSON.stringify(out));
"""


def test_the_summary_says_so_when_no_fork_was_clicked():
    """An untouched form must not read as agreement; a click or a keyboard choice counts."""
    import json
    import subprocess

    node = node_or_skip()
    program = "const SCRIPT = " + json.dumps(answer_script()) + ";\n" + FORM_HARNESS
    result = subprocess.run([node, "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    warning = "No fork was clicked"
    assert warning in out["untouched"], out["untouched"]
    assert warning in out["freeTextOnly"] and "Not on the page: a reframe" in out["freeTextOnly"]
    assert warning not in out["confirmed"] and "kept the recommendation" in out["confirmed"]
    keyboard = out["changedByKeyboard"]
    assert warning not in keyboard and "CHANGED from (a)" in keyboard
    assert warning not in out["oneOfTwoClicked"], "the warning is for a form with no fork clicked"
    old_draft = out["oldDraftChanged"]
    assert warning not in old_draft and "CHANGED from (a)" in old_draft, old_draft


def test_a_first_component_page_freezes_with_its_spec_not_its_spec_map():
    """It feeds /deconstruct and then /adr-spec, so freezing at the map would strand the second."""
    flat = {
        path: " ".join((ROOT / path).read_text(encoding="utf-8").split())
        for path in (
            "thinking/fusion/SKILL.md",
            "sdd/deconstruct/SKILL.md",
            "docs/sdd-workflow.md",
            "templates/profile.md",
        )
    }
    assert "freezes only when its spec is approved" in flat["thinking/fusion/SKILL.md"]
    assert "until the spec or spec map it feeds is approved" not in flat["thinking/fusion/SKILL.md"]
    assert "cite the page's new commit" in flat["sdd/deconstruct/SKILL.md"]
    assert "a first-component page, once its spec is" in flat["docs/sdd-workflow.md"]
    assert "(a first-component page, once its spec is)" in flat["templates/profile.md"]
