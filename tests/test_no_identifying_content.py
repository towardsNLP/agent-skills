"""This repository is publishable. Nothing in it may identify a client or a colleague.

Three guards, because a name enters in three different shapes.

`test_fixture_identities_are_invented` reads **shape**: every capitalised name-shaped pair
inside `tests/` must be declared here. It is an allow-list, not a deny-list, and that choice
is the point: a deny-list would have to spell out the very names it exists to keep out of a
public repository.

`test_identity_fields_name_only_invented_people` reads **position**, because shape alone let
a real first name sit in this suite and in the sample board in `README.md`: it was lowercase
and one word, so no name-shaped pattern could tell it from a noun. What gave it away was
where it sat. The claim field, the contributor argument, a state file, a diary filename --
each of those positions holds a person by definition, so whatever sits there must resolve to
a declared invented person, in any capitalisation and at any word count.

`test_the_authors_name_appears_only_where_authorship_is_declared` reads **location**, and it
exists because shape and position together still missed a leak. A prose comment in
`session/start-session/scripts/context_packet.py` illustrated slug matching with the author's
own first name and surname slug, lowercase. Shape could not see it (shape is scoped to
`tests/`), and position could not see it (a code comment is not an identity field). What is
checkable is *where* the name is allowed: four files declare authorship, and the name may
appear in those and nowhere else. That is still an allow-list, of locations rather than
names, so it publishes nothing the LICENSE does not already say.

**What none of the three catches, stated plainly rather than left to be discovered:** a
colleague's or client's name that is lowercase, one word, and sits outside `tests/` and
outside an identity field. "A project sat there for a whole migration" read as prose in a
docstring in this suite for weeks, with a real project named instead of "a project". No
committable guard can close that, for the reason the allow-list note above gives: the
deny-list would have to spell out the names. **Screen it before committing, from a list kept
outside this repository.**

Shape stays scoped to `tests/`, because that is where identifying data actually enters: a
fixture wants a realistic contributor, and the nearest realistic name is a colleague's. That
is exactly how a real one reached this suite once. Position is scoped repo-wide, since the
sample board in `README.md` carried the same leak that the suite did -- minus the vendored
skills, whose text is pinned by hash in `UPSTREAM.toml` and cannot be edited here without
forking them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import tomllib

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

# Values that sit in an identity position without naming anyone. "Dan" is a deliberate
# truncation of an invented name, used to prove that a substring of a roster entry is not a
# contributor; it is not a person, and nobody may add one here that is.
DECLARED_NON_PEOPLE = {
    "Dan",
}

# What a claim field says for "nobody has this". `_NONE` in the startup helper and
# `NONE_WORDS` in the status tool hold the same set; a word here only has to name nobody.
NONE_WORDS = {"", "-", "—", "none", "n/a", "not selected", "unclaimed"}

_NAME_SHAPED = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")

# Identity positions. Every one of these holds a person, so its value is read whatever its
# case and however many words it has -- the gap that shape-matching alone left open.
_IDENTITY_POSITIONS = (
    # `claim="..."`, `contributor="..."`, `CONTRIBUTOR = "..."`, `claimed_by == "..."`
    re.compile(
        r"(?:\w+_)?(?:claim|claimant|claimed_by|contributor)s?\s*={1,2}\s*[a-z]{0,2}[\"']([^\"']*)[\"']",
        re.I,
    ),
    re.compile(r"--contributor[=\s]+(\"[^\"]*\"|'[^']*'|\S+)"),
    # The colon is required: `**Claimed by:** <value>` is a field, while `**Claimed by** is
    # the one status a human writes` is prose about the field, and its value is a sentence.
    re.compile(r"^\s*(?:[-*]\s*)?\*\*claimed[ _]by(?::\*\*|\*\*:)\s*(.*)$", re.I | re.M),
    # The status board prints the claim last: `   01 <title> done    gate    <claim>`. The
    # whitespace classes exclude the newline deliberately: under `re.M`, `\s` crosses lines
    # and this pattern then captured the closing code fence instead of the claim column.
    re.compile(r"^[^\S\n]+\d{2}[^\S\n]+\S.*?[^\S\n](\S+)[^\S\n]*$", re.M),
    # A contributor's state file and diary are named after them by convention.
    re.compile(r"(?:state|diaries)/([A-Za-z][\w.-]*)\.md"),
)


def declared_handles() -> set[str]:
    """Every way a fixture writes a declared person: full name, first name, state slug.

    The forms `same_person` compares a claim against, so a name this guard accepts is one
    the helper can still recognise. The hyphenated full name is here because
    `templates/profile.md` documents it as the state convention's own answer to a first-name
    collision, so `dana-reed.md` is a filename the convention produces rather than a new
    identity. **This widens nothing on its own:** the loop reads only names already declared
    invented, so a real person still has to be declared before any of their forms pass.
    """
    handles = {name.casefold() for name in DECLARED_NON_PEOPLE}
    for name in DECLARED_FIXTURE_NAMES:
        words = name.split()
        # The unstripped first name is kept as well as the stripped one. Dropping it would
        # narrow the guard for any declared name whose first part carries punctuation:
        # `D'Arcy Vale` would stop accepting `d'arcy` and start failing on its own fixture.
        # No declared name has that shape today, which is exactly why it would go unnoticed.
        first = words[0].casefold() if words else ""
        parts = [re.sub(r"[^a-z0-9]+", "", word.casefold()) for word in words]
        parts = [part for part in parts if part]
        handles.update({name.casefold(), first, *parts[:1], "-".join(parts)})
    return handles


def people_named(value: str) -> list[str]:
    """The person parts of an identity value, read by the conventions the readers use.

    A claim carries its branch after an em dash (`docs/sdd-workflow.md`), a documented field
    offers alternatives with `|`, and a roster lists one person per line. Each part is judged
    on its own. A placeholder, an interpolation and a none-word all name nobody.
    """
    people: list[str] = []
    for alternative in re.split(r"[|,\n]", value):
        person = alternative.split("—", 1)[0].split(" -- ", 1)[0]
        person = person.strip().strip("\"'`*").strip()
        person = re.sub(r"-diary$", "", person).strip()
        if not person or person.casefold() in NONE_WORDS:
            continue
        if re.search(r"[<>{}]", person):  # `<name>`, `{claimant}`: a slot, not a person
            continue
        people.append(person)
    return people


def scanned_files() -> list[Path]:
    """Repo-authored Python and Markdown, minus the skills this repo only vendors."""
    manifest = tomllib.loads((ROOT / "UPSTREAM.toml").read_text(encoding="utf-8"))
    vendored = {
        ROOT / skill["local_path"]
        for skill in manifest.get("skills", [])
        if skill.get("status") == "vendored"
    }

    files: list[Path] = []
    for pattern in ("tests/**/*.py", "tools/**/*.py", "session/**/*.py", "**/*.md"):
        files.extend(sorted(ROOT.glob(pattern)))
    return [
        path
        for path in dict.fromkeys(files)
        if not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
        and not any(directory in path.parents for directory in vendored)
    ]


def test_the_authors_name_appears_only_where_authorship_is_declared() -> None:
    """The author's name is metadata, not content, and it belongs only in the metadata.

    Read from `plugin.json` rather than written here, so this guard adds no occurrence of
    its own. `LICENSE`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`
    carry it legitimately and are outside `scanned_files()` already; `docs/sdd-workflow.md`
    is inside it and carries an Authors line, so it is named below.

    Both the full name and each of its parts are checked, case-insensitively, because the
    leak this closes was a lowercase first name and a lowercase surname inside a code
    comment: `<first>` finds `<first>-<surname>.md`, written as an example of slug matching.
    An example in a shipped skill must use a declared invented identity, like every fixture.
    """
    author = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    parts = [part for part in author["author"]["name"].split() if len(part) > 2]
    assert parts, "plugin.json declares no author name to check against"

    allowed = {ROOT / "docs/sdd-workflow.md"}
    offenders: dict[str, list[str]] = {}
    for path in scanned_files():
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        for part in parts:
            for match in re.finditer(rf"(?<![\w-]){re.escape(part)}(?![\w-])", text, re.I):
                line = text.count("\n", 0, match.start()) + 1
                offenders.setdefault(f"{path.relative_to(ROOT)}:{line}", []).append(part)

    assert not offenders, (
        f"the author's name appears outside the files that declare authorship: {offenders}. "
        "Use a declared invented identity from DECLARED_FIXTURE_NAMES instead. If a new file "
        "genuinely declares authorship, add it to `allowed` here and say why."
    )


def test_fixture_identities_are_invented() -> None:
    allowed = DECLARED_FIXTURE_NAMES | DECLARED_NON_NAMES
    found: dict[str, set[str]] = {}

    for path in sorted(ROOT.glob("tests/**/*.py")):
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


def test_a_lowercase_one_word_claim_is_still_read_as_a_person() -> None:
    """The gap shape-matching left open, and the reason the second guard exists.

    A name-shaped pattern cannot tell `claim="robin"` from a noun. The position can, so the
    reader must return the value whatever its case and however few words it has.
    """
    found = [
        person
        for position in _IDENTITY_POSITIONS
        for match in position.finditer('            claim="robin",')
        for person in people_named(match.group(1))
    ]

    assert found == ["robin"]


def test_the_board_column_and_the_state_filename_are_identity_positions() -> None:
    """Both carried the leak once: the sample board in `README.md`, and a fixture's state."""
    board = "   01 the loader rejects an ungoverned predicate done    gate    robin\n"
    state = 'write(tmp_path / "planning/agent/state/robin.md", "")'

    found = {
        person
        for text in (board, state)
        for position in _IDENTITY_POSITIONS
        for match in position.finditer(text)
        for person in people_named(match.group(1))
    }

    assert found == {"robin"}


def test_a_slot_or_a_none_word_names_nobody() -> None:
    """Mutation guard: a reader that flags every field would be silenced, not tightened."""
    assert people_named("{claimant}") == []
    assert people_named("<name — branch> | unclaimed") == []
    assert people_named("unclaimed") == []
    # The claim carries its branch after an em dash, spaced or tight; the name is what is left.
    assert people_named("Morgan Vale — `morgan-vocabulary-12`") == ["Morgan Vale"]
    assert people_named("Morgan Vale—`morgan-vocabulary-12`") == ["Morgan Vale"]


def test_identity_fields_name_only_invented_people() -> None:
    allowed = declared_handles()
    found: dict[str, set[str]] = {}

    for path in scanned_files():
        if path.name == Path(__file__).name:
            continue  # the allow-list itself is the one file that may name names
        text = path.read_text(encoding="utf-8")
        for position in _IDENTITY_POSITIONS:
            for match in position.finditer(text):
                for person in people_named(match.group(1)):
                    if person.casefold() not in allowed:
                        found.setdefault(person, set()).add(str(path.relative_to(ROOT)))

    undeclared = {person: sorted(files) for person, files in found.items()}
    assert not undeclared, (
        f"undeclared name(s) in a claim, contributor, state or diary position: {undeclared}. "
        "A value in one of those positions is a person by definition, whatever its case. "
        "If it is an invented fixture identity, declare it in DECLARED_FIXTURE_NAMES. "
        "If it is a real person, remove it — this repository is publishable."
    )
