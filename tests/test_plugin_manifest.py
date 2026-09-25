"""`plugin.json` declares a set that can actually run.

**The defect this exists to prevent, and it shipped.** Until 0.5.0 the manifest declared nine
skills, and three of them refused to do their job without a skill that was **not declared**:
`adr-spec` will not write §3 Scope or §5 Seams without a grilling and says *"Run `/grill-me`"*;
`deconstruct` forbids authoring a glossary term and hands the gap to `domain-modeling`;
`implement` says *"Use `/tdd`"*. Anyone who installed the plugin without also holding the
personal set got a workflow that stopped at its first real step, and nothing here reported it.

Two properties, both cheap, neither previously asserted:

1. every declared skill exists on disk, with a `SKILL.md`
2. every skill a declared skill tells the user to run is **itself declared**

The second is the one that matters. It is what makes the manifest a closed set rather than a
list someone remembers to extend.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"

#: Slash-commands in skill prose that are NOT skills in this repository, so they cannot be
#: declared here. Each is named with its reason rather than matched by a pattern: a pattern
#: would also swallow the next genuine omission, which is the failure this module exists to
#: catch.
NOT_OURS = {
    "code-review": "a Claude Code built-in, not a skill in this repository",
    "compact": "a Claude Code built-in",
    "clear": "a Claude Code built-in",
    "context": "a Claude Code built-in",
    "plugin": "a Claude Code built-in",
}


def declared() -> list[str]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["skills"]


def test_every_declared_skill_exists():
    missing = [s for s in declared() if not (ROOT / s / "SKILL.md").is_file()]
    assert not missing, f"declared in plugin.json with no SKILL.md on disk: {missing}"


def test_the_manifest_is_not_empty():
    """Without this, both assertions below pass over an empty list and inspect nothing."""
    assert len(declared()) >= 12, (
        f"only {len(declared())} skills declared. If one was deliberately removed, change this "
        f"floor in the same commit and say why"
    )


def test_a_declared_skill_never_depends_on_an_undeclared_one():
    """The 0.4.1 defect: `/grill-me`, `/tdd` and `domain-modeling` were required and undeclared.

    Reads the prose of each declared skill for a `/name` invocation and for a bare
    `domain-modeling`-style reference, and requires the target to be declared too. A plugin
    that tells the user to run something it does not ship is a plugin that stops working at
    that line.
    """
    names = {Path(s).name for s in declared()}
    wanted: dict[str, set[str]] = {}
    for skill in declared():
        text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        refs = set(re.findall(r"`/([a-z][a-z0-9-]+)`", text))
        # `domain-modeling` is referred to by bare name rather than as a slash-command.
        refs |= {
            m
            for m in re.findall(r"`([a-z][a-z0-9-]*-[a-z0-9-]+)`", text)
            if m in {d.split("/")[-1] for d in _all_skill_dirs()}
        }
        refs -= {Path(skill).name}
        refs -= set(NOT_OURS)
        undeclared = refs - names
        if undeclared:
            wanted[skill] = undeclared
    assert not wanted, (
        f"declared skills require skills the manifest does not ship: {wanted}. Either add them "
        f"to plugin.json's `skills`, or stop the prose telling the user to run them"
    )


def _all_skill_dirs() -> list[str]:
    groups = ("session", "sdd", "thinking", "knowledge", "craft")
    return [str(p.parent.relative_to(ROOT)) for g in groups for p in (ROOT / g).rglob("SKILL.md")]


def test_the_dependency_check_would_notice_an_undeclared_skill():
    """Mutation guard: prove the comparison is live.

    Asserting that some invented name is undeclared would be true of the invented name
    whatever the manifest says. This drops a really-declared skill from the set and asserts the
    comparison reports exactly it.
    """
    names = {Path(s).name for s in declared()}
    assert "grill-me" in names, "the fixture itself is broken"
    text = (ROOT / "sdd" / "adr-spec" / "SKILL.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"`/([a-z][a-z0-9-]+)`", text)) - set(NOT_OURS)
    assert "grill-me" in refs, "adr-spec no longer names grill-me; this guard is now vacuous"
    assert refs - (names - {"grill-me"}) == {"grill-me"}
