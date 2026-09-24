"""This repository is publishable. Nothing in it may identify a client or a colleague.

The guard is an allow-list, not a deny-list, and that choice is the point: a deny-list
would have to spell out the very names it exists to keep out of a public repository. So
instead every capitalised name-shaped pair inside `tests/` must be declared here, and a
new one fails until someone declares it deliberately.

Scoped to `tests/` because that is where identifying data actually enters — a fixture
wants a realistic contributor, and the nearest realistic name is a colleague's. That is
exactly how a real one reached this suite once. Skill and reference text is scoped out:
it carries cited authors (Matt Pocock, Michael Feathers, Greg Nuckols) in files pinned
by hash in `UPSTREAM.toml`, which cannot be edited here without forking them.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Invented people, used by fixtures. Add a name here only if you made it up.
DECLARED_FIXTURE_NAMES = {
    "Dana Reed",
    "Morgan Vale",
}

# Capitalised pairs that are products, headings or prose rather than people.
DECLARED_NON_NAMES = {
    "Agent Skills",
    "Claude Code",
    "Session card",
}

_NAME_SHAPED = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")


def test_fixture_identities_are_invented() -> None:
    allowed = DECLARED_FIXTURE_NAMES | DECLARED_NON_NAMES
    found: dict[str, set[str]] = {}

    for path in sorted((ROOT / "tests").glob("*.py")):
        if path.name == Path(__file__).name:
            continue  # the allow-list itself is the one file that may name names
        for match in _NAME_SHAPED.findall(path.read_text(encoding="utf-8")):
            found.setdefault(" ".join(match.split()), set()).add(path.name)

    undeclared = {name: sorted(files) for name, files in found.items() if name not in allowed}
    assert not undeclared, (
        f"undeclared capitalised name(s) in tests/: {undeclared}. "
        "If it is an invented fixture identity, declare it in DECLARED_FIXTURE_NAMES. "
        "If it is a real person, remove it — this repository is publishable."
    )
