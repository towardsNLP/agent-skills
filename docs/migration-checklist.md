# Adopting the workflow in an existing repo

Each item names **what** and **done when** — a condition you can check, not a box to tick. That is
deliberate: boxes measurably do not get ticked, so the last group is a command that either exits
zero or tells you what is still wrong.

Run it top to bottom. Group F applies only where the repo ships planning material to a client.

---

## A — Before anything

**A1. Cut a branch.** Never on trunk. If an open PR already touches `.claude/skills/`, the profile
or the spec template, **base this branch on that PR's head** rather than trunk: the overlap is
total and rebasing later is cheaper than resolving a conflict in every file at once.
*Done when:* `git branch --show-current` is the new branch and its base is the right commit.

**A2. Decision records exist.** `planning/adr/` with a README stating the bar and the format.
*Done when:* the directory exists and the README names what does and does not qualify.

**A3. Vocabulary is settled.** A glossary, or a contracts document acting as one.
*Done when:* the profile names `glossary_path` or `contracts_path`, and it resolves.
*If it does not:* stop and run `domain-modeling`. `/deconstruct` refuses to proceed without it, and
a component set built on unsettled vocabulary decomposes along the wrong lines.

---

## B — The profile

The skills hold the workflow; the profile holds the facts. Every key below is read by at least one
skill, and a missing one makes that skill guess.

**B1.** `project_mode` — `software`, `data-science`, `knowledge-engineering` or `mixed`
**B2.** `spec_map_path` — `planning/spec-map.md`
**B3.** `spec_path_pattern` — `planning/specs/<spec-id>/spec.md`, one directory per spec
**B4.** `ticket_dir` — `planning/tickets/<spec-id>/`, deliberately **outside** `spec_dir`
**B5.** `decision_records` — `planning/adr/`
**B6.** `sme_register_path` — the file a `check_type: sme` ticket points a row at, or omit
**B7.** `ticket_status_command` — e.g. `make ticket-status`
**B8.** `spec_migration_mode` — `big-bang` or `on-touch`
**B9.** `test_command` — only where the runner is not `pytest`
**B10.** `authority_map` and `doc_precedence_order` — every governed name resolves to one owner
**B11.** Data and knowledge pointers — registries, contracts, competency questions, constraints
and reproducibility command where they apply

*Done when:* `grep -c '^\- \*\*' planning/agent/profile.md` accounts for all of them, and
`ticket_status.py` parses the file without falling back to a default.

---

## C — Structure

**C1. Create `planning/spec-map.md`.** Run `/deconstruct`, or hand-write the table where the
components are already known — most repos have this buried in a roadmap section already.
*Done when:* every existing spec has a row, and every row has its blocking edges.

**C2. Create `planning/tickets/`.** Empty is fine; it is the write target for `/tickets`.

**C3. Convert specs to directories.** `planning/specs/spec-<id>-<slug>.md` becomes
`planning/specs/<id>-<slug>/spec.md`. Use `git mv` so history follows.
*Done when:* no loose `.md` remains directly under `planning/specs/`.

**C4. Split post-approval records out.** Every spec may have `amendments.md`, owned by
`/adr-spec`, and gets `acceptance.md` at close from `/implement`. Move dated amendments to the
first and compliance results to the second.
*Done when:* no spec body contains a dated amendment or a compliance results table, and each file
has one writer.
*Why:* `spec.md` is frozen at approval. Amendments must remain visible to ticketing and
implementation without interleaving into the blueprint or final compliance record.

**C5. Update the spec template.** No task table; seams and acceptance in one section; `Kind` and
`Parent` frontmatter fields; amendment and compliance records split into their owned files.

---

## D — Skills

**D1.** Replace `to-spec` with `adr-spec`. `git mv` the directory, then overwrite the contents.
**D2.** Add `deconstruct`, `tickets`, `implement`.
**D3.** Update the skills README: the six names, what each does, and that this is a copy.
**D4.** *Done when:* `diff -r` between the repo's `.claude/skills/` and the canonical source shows
no difference for any shared skill. A silent fork is how one repo ends up running a workflow the
others have already fixed.

---

## E — Tooling

**E1. Vendor the status script.** `make sync-tools TO=<repo>` from the skills repo.
**E2. Add the target** the profile names — `ticket-status` in the Makefile.
**E3. Wire CI** to run it. The non-zero exit is the drift detector, and a detector nobody runs is
a detector that does not exist.
**E4. Guard the copy.** CI diffs the vendored script against its source, or a stale fork goes
unnoticed.

---

## F — Client boundary (skip where there is none)

**F1. Withhold the ticket tree.** If the repo's export manifest forbids globs, this is why
`ticket_dir` sits outside `spec_dir`: one directory line covers every spec, forever, and a new
spec cannot ship by omission.

**F2. Fix spec-path references in shipped artifacts.** Measure first — the two numbers are very
different. `grep -rl 'planning/specs/'` finds what breaks on a rename; `grep -rl 'spec-<id>'`
finds what does not. IDs survive; paths do not.
*Then adopt the rule:* **reference specs by ID from now on, never by path.**

**F3. Never convert a closed spec.** Its path may already be cited by something the client holds,
and that cannot be retro-fixed. Under `on-touch`, a spec converts when next amended or closed —
and a spec that is already closed is simply done.

---

## G — Verify

**G1.** `<ticket_status_command>` runs. Exit zero, or every line of its drift output is understood
and expected.
**G2.** The existing test suite passes.
**G3.** Any doc-consistency test the repo already has still passes — a word budget, a symlink
check, an export-boundary test.
**G4.** Skill discovery: the new skills appear. Restart the session and confirm, rather than
assuming the copy took.

---

## What this list deliberately does not do

**It does not triage spec content.** Moving contract-level design into the constitution, and
dropping implementation detail that should never have been written, is judgement work on every
spec individually. It is the migration's real value and it does not belong on a checklist.
Structure first, content second, and the content pass wants a human on each spec.
