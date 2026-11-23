"""The README is the repository's front door; what it shows and prints must exist.

A newcomer copies the commands the README prints and follows its links before anything else. A
command that names no skill fails at the first step, as a display-name mismatch once broke another
skill pack's main command, and a figure that does not render leaves a gap where the argument was.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
FIGURES = ROOT / "docs" / "figures"


def declared_skills() -> set[str]:
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return {path.rstrip("/").split("/")[-1] for path in manifest["skills"]}


def test_every_printed_plugin_command_names_a_declared_skill():
    commands = set(re.findall(r"/sdd:([a-z][a-z-]*)", README))
    assert commands, "the README prints no /sdd: commands"
    unknown = commands - declared_skills()
    assert not unknown, f"the README prints commands no skill answers: {sorted(unknown)}"


def test_every_printed_command_matches_its_skill_name():
    """A host invokes a skill by the name in its SKILL.md; a folder name that differs fails."""
    for name in set(re.findall(r"/sdd:([a-z][a-z-]*)", README)):
        skill = next(ROOT.glob(f"*/{name}/SKILL.md"))
        declared = re.search(r"^name:\s*(\S+)", skill.read_text(encoding="utf-8"), re.M)
        assert declared and declared.group(1) == name, (name, declared and declared.group(1))


def test_every_relative_link_and_image_resolves():
    targets = re.findall(r"\]\((?!https?://|#|mailto:)([^)#\s]+)", README)
    missing = [target for target in targets if not (ROOT / target).exists()]
    assert not missing, f"broken links in README.md: {missing}"


def test_every_readme_figure_is_used_and_stands_alone():
    used = set(re.findall(r"\]\(docs/figures/([\w-]+\.svg)\)", README))
    present = {path.name for path in FIGURES.glob("*.svg")}
    assert used == present, f"unused: {present - used}; missing: {used - present}"
    for alt in re.findall(r"!\[([^\]]*)\]\(", README):
        assert alt.strip(), "every figure in the README needs alt text"
    for path in FIGURES.glob("*.svg"):
        svg = path.read_text(encoding="utf-8")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg, path.name
        assert "<title" in svg and 'class="bg"' in svg, path.name
        assert "prefers-color-scheme: dark" in svg, path.name
        for borrowed in ("var(--hz-", "light-dark(", "color-mix(", "var(--background"):
            assert borrowed not in svg, (path.name, borrowed)
        used_vars = set(re.findall(r"var\((--fz-[a-z-]+)\)", svg))
        assert used_vars <= set(re.findall(r"(--fz-[a-z-]+):", svg)), path.name


def test_the_readme_leads_with_why_and_the_workflow_before_install():
    """F2 (a): the reader's path. Why, then the workflow, then a first run, then install."""
    headings = re.findall(r"^## (.+)$", README, re.M)
    order = [
        "Why: the check before the work",
        "The workflow on one screen",
        "A first run",
        "Install",
    ]
    positions = [headings.index(heading) for heading in order]
    assert positions == sorted(positions), headings
