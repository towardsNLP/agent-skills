# The SDD workflow: deconstruct → spec → ticket → implement → ship

Authors: Ahmad Hashemi & Claude (Anthropic)
Settled 2026-09-22. The earlier vocabulary ("slice") is retired in favour of "ticket".

This is the design. No skill has been written against it yet.

---

## 1. The move underneath everything

DDD, SDD, TDD and pre-registration are one move at four altitudes: **commit to the check before
doing the work.** Each altitude differs only in what the check is made of.

| Altitude | The check, committed first |
|---|---|
| **DDD** — vocabulary | the term's definition: necessary and sufficient conditions |
| **Deconstruction** — project | the component's boundary and its dependency edges |
| **SDD** — feature | the spec's acceptance criteria, attached to named seams |
| **TDD** — unit | a failing test at the pre-agreed seam |
| **Pre-registration** — experiment | the predicate and its baseline, fixed before the run |

DDD is upstream of all of it: you cannot spec what you cannot name.

Three consequences run through every decision below, and each one is this move applied:

- **Doneness is derived, never written.** The check was committed up front, so asking a human to
  restate its result is both redundant and unreliable.
- **Build-level design is not pre-written.** Committing to the *implementation* is the one thing
  this move does not ask for. It is waterfall wearing SDD's clothes.
- **Re-ticketing is normal; re-speccing is an amendment.** Tickets sit below the committed check
  and may be recut freely. The spec *is* the commitment.

## 2. The pipeline

```
/deconstruct  →  grill  →  /adr-spec  →  /tickets  →  /implement  →  review → integrate → ship
   project                 ─── one session ───          one fresh session per ticket
```

- `/deconstruct` is a project-level act, run rarely.
- **Grilling, `/adr-spec` and `/tickets` run in one session.** The interview is the thought that
  makes the spec trustworthy, and the seams it settles are what makes a ticket sizeable. Splitting
  the session throws that context away.
- **Each `/implement` gets a fresh session.** That is what "sized to one context window" is for.

## 3. The artifacts

| Artifact | Written by | Lifetime | Path |
|---|---|---|---|
| Spec map | `/deconstruct`, amended by hand | project | `planning/spec-map.md` |
| ADR | `/adr-spec` proposes, human approves | forever | `planning/adr/NNNN-slug.md` |
| Spec | `/adr-spec` | **immutable after approval** | `planning/specs/<spec-id>/spec.md` |
| Acceptance record | `/implement` at spec close | append-only | `planning/specs/<spec-id>/acceptance.md` |
| Ticket | `/tickets`; closed by `/implement` | durable | `planning/tickets/<spec-id>/NN-slug.md` |
| Contracts / glossary | `domain-modeling`, human-ruled | forever | per profile |

**Tickets are internal.** They live outside `planning/specs/` so the client boundary is a
directory line enforced by an existing test, not a per-spec manifest entry that ships by omission.

## 4. Layout

```
planning/
  PLAN.md  roadmap.md  STATE.md
  spec-map.md                         the planned component set + dependency edges
  adr/NNNN-slug.md                    decisions (sandcastle format)
  references/                         glossary, contracts — the constitution
  specs/<spec-id>/spec.md             blueprint, frozen
  specs/<spec-id>/acceptance.md       close record + amendment log
  tickets/<spec-id>/NN-slug.md        tracking records (internal)
  diaries/  agent/  templates/  notes/
```

`spec.md` has two commits: created, approved. Everything that happens afterwards goes in
`acceptance.md`. This is structural, not a convention — an amendment cannot interleave into a
blueprint it is not allowed to open.

## 5. The spec

A **high-level blueprint for a feature.** Why · product anchor · scope (IN/OUT/DEFERRED) ·
inputs and outputs · seams · acceptance · risks · references.

Frontmatter carries `Kind: build | experiment`, `Parent` (the roadmap row or PLAN section it
expands), and `Anchors` extended to cite ADRs and contract sections. The reverse link is never
written: `grep -l 'adr/0002' planning/specs/` computes it.

Design detail has **three destinations and no fourth**: a **contract** if others build against it,
an **ADR** if it was a hard-to-reverse decision, or **nowhere** if it is implementation. On this
rule the worked example below splits 635 lines to the constitution, 175 lines never written, and
leaves roughly 330.

For `Kind: experiment`, §3 becomes Hypothesis / Controls / Not varied and acceptance leads with
the registered predicate and its baseline. An experiment spec decomposes into the same ticket
object — one arm, one ticket, `check_type: gate`, the check being the predicate. Expect
experiment specs to be **re-ticketed mid-flight**; you cannot write the ablation's ticket until
arm 1 has run.

## 6. The ticket

A **tracking record used to manage the work**, not a design document.

```markdown
# NN — <title>

**What becomes true:** what is the case once this lands
**Blocked by:** NN, NN — or "none (can start immediately)"
**Governs:** contract §X, adr/NNNN
**check_type:** test | gate | sme | manual
**check:** `<pytest node | command | SME register row | procedure>`
**Claimed by:** <name — branch> | unclaimed

## Approach (non-binding, ≤150 words)
- what the author had in mind; the implementer may depart without an amendment

## Outcome
<!-- written once, by the implementing session at close -->
**PR:** #NN
**Diverged:** what differed from the blueprint, or "nothing"
```

Rules:

- **Independently verifiable, and the check is what makes it so.** This replaces vertical slicing:
  verticality is how you get independent verifiability when the deliverable has a user-facing
  surface, and most of this work does not have one.
- **Sized to one fresh context window.**
- **Exactly one path is permitted: the check.** A path with a test behind it fails loudly; an
  incidental `src/foo.py:42` rots in silence.
- No code snippets, except one that encodes a decision more precisely than prose can — a schema, a
  state machine, a type shape.
- Prefactoring tickets come first: make the change easy, then make the easy change.
- **Wide refactors are the exception** — one mechanical change whose blast radius fans across the
  codebase. Sequence as expand–contract: add the new form beside the old, migrate in batches sized
  by blast radius (each batch its own ticket), delete the old form last.
- **`/tickets` never edits the spec.** This is what makes "frozen" mechanical.
- The 150-word `Approach` cap is the whole mechanism. Without a bound it grows back into §5.

## 7. Written vs derived

**Write only what a script cannot compute.**

| Written | Derived |
|---|---|
| the claim (who has it, which branch) | doneness |
| the approach hint | ticket and spec counts |
| the outcome and what diverged | whether a check still resolves |
| the planned component set | which specs are owed, which lack tickets |

`tools/ticket_status.py` dispatches on `check_type`: run tests, run gates, grep the SME register,
report `manual` as always-unknown. It **exits non-zero** when a ticket carries an Outcome but its
check fails, when a check no longer resolves, when a spec in the map has no directory, or when a
spec directory has no tickets. That exit code is the drift detector, and it is the reason the
script exists.

It is vendored: the plugin holds the source, each project keeps a copy at `tools/ticket_status.py`
synced by `make sync-tools`, with CI checking the copy matches. A plugin-only script cannot run in
GitHub Actions. Package it with pip at the third adopter, not before.

## 8. The skills

| Skill | Reads | Writes | Never touches |
|---|---|---|---|
| `/deconstruct` | PLAN, roadmap, glossary, code | `spec-map.md` | specs, ADRs |
| `/adr-spec` | the spec-map row, contracts, existing ADRs, glossary | ADRs (one at a time, each approved), then `spec.md` | tickets, other specs |
| `/tickets` | one spec + the contracts it cites | `tickets/<spec-id>/NN-*.md` | **the spec** |
| `/implement` | one ticket + its spec + the contracts it names | code, tests, the ticket's Outcome, `acceptance.md` at spec close | the spec body, other tickets |

`/deconstruct` requires the glossary and flags missing vocabulary but never authors it — that is
`domain-modeling`'s job, which keeps DDD genuinely upstream.

`/adr-spec` writes the decisions **before** the spec, because a spec written before its decisions
settle has to be amended when they do. It proposes each ADR against the four-part bar in
`adr/README.md`; **the human rules on each one.**

`/implement` closes the ticket by *demonstrating* done, never declaring it: run the check, record
the outcome and any divergence, record the PR, release the claim. The file stays where it is — the
PR points at that path, and the divergence record is the ticket's most durable content.

Profile keys the skills read (all present in `templates/profile.md`): `spec_map_path`, `ticket_dir`, `ticket_status_command`, `sme_register_path`,
`spec_migration_mode`, and `spec_path_pattern` updated to `planning/specs/<spec-id>/spec.md`.

## 9. Where this diverges from Pocock, and why

Adopted wholesale: *tracer bullet*; blocking edges and working the frontier; one-context-window
sizing; prefactoring first; expand–contract for wide refactors; "do not modify the parent"; the
step-4 quiz; the prototype-snippet exception.

| Divergence | Why |
|---|---|
| Tickets are durable, not `.scratch/` | they carry the divergence record, which outlives the work |
| Independently verifiable, not vertically sliced | most of this work has no user-facing surface |
| No acceptance checkboxes; doneness derived | 95 boxes written across three repos, 0 ever ticked |
| One path allowed (the check) | a path with a test behind it cannot rot silently |
| No user stories | wrong shape for interfaces, invariants and measurements |
| No issue tracker | local files, and the export boundary makes a tracker the wrong home |
| The spec skill authors ADRs | five ADRs in one repo had to be rescued after the fact, because nothing asked for them |
| Design promoted to contracts | 78% of the worked example's design section was contract, not build |

His `implement` skill is five lines and never touches the ticket — coherent for a tracker-published
throwaway, and the reason the close act had to be designed here.

## 10. The evidence

Every decision above traces to a measurement, not a preference:

- The largest spec in one repository, a rule engine: 10,821 words / 1,139 lines. Its design section
  is 811 lines — **635 contract, 175 build**. The task table is 44 lines, 3.9%. Extracting tickets
  would have saved 4%. This is the worked example referenced above.
- **95 unchecked acceptance boxes across three repositories. Zero ticked. Ever.**
- The largest spec in a second repository: 12,001 words carrying **ten amendments interleaved into
  three different sections**. Specs in that repo say "amendment" 90 times.
- **Across three repositories, no spec cited a single ADR.** One had five on disk; two had no
  `planning/adr/` at all.
- One roadmap's spec catalogue records, in its own header, the failure it was built to prevent: a
  spec's task needed two other specs and neither had been written. The catalogue existed; it was
  hand-maintained. The same content existed three times over — in that roadmap, in an 8,799-word
  component tracker beside it, and again in a second repository's roadmap.
- A client export manifest forbids globs by design, so co-locating tickets under `planning/specs/`
  would make each new spec directory **ship by omission** — the failure that manifest exists to
  prevent.

## 11. Not decided

- Whether the spec map replaces an existing hand-maintained component tracker or absorbs part of it.
- What `check_type: manual` reporting looks like once there are enough of them to matter.
- Roadmaps carrying stacked "prior state" blocks in place of a single current state — a separate
  cleanup, and not this design's problem to solve.
