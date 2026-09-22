---
name: adr-spec
description: Record the decisions, then write the spec against them. Two layers in order — ADRs first, each approved by the user, then a frozen blueprint. Refuses the sections that need deliberate thought unless a grilling preceded it.
disable-model-invocation: true
---

# ADR-spec

Two layers, in this order: **the decisions, then the blueprint that assumes them.** A spec written
before its decisions settle has to be amended when they do, which is how a blueprint turns into an
archaeological dig.

Read `planning/agent/profile.md` for `spec_dir`, `spec_path_pattern`, `spec_template_path`,
`spec_owner`, `spec_initial_status`, `workstream_id_scheme`, `phase_vocabulary`, `roadmap_path`,
`spec_map_path`, `contracts_path`, `glossary_path` and `decision_records`.

## The precondition

**Do not write §3 Scope or §5 Seams and acceptance unless a grilling preceded this in the same
context.** Those two carry the thinking; pre-filled, they get approved without being read, which
is worse than empty.

No grilling in context means create the shell, fill §1 and §2 from what the conversation supports,
leave the rest as placeholders, and say: *"§3 and §5 are unfilled. Run `/grill-me` and re-run
this, or fill them by hand."* Do not interview the user here — that is grilling's job and it does
it better.

Keep grilling, this skill and `/tickets` in **one unbroken context window**. Don't compact between
them.

## Step 1 — Check nobody has already specified this

Grep `spec_dir` for a spec covering the same subject, and `spec_map_path` for a row already
claimed. A duplicate ID is refused by `check-contracts`; a duplicate *subject* under a fresh ID is
not, and is the more expensive mistake. If one exists, stop and say so: supersede or extend is the
user's call.

## Step 2 — Settle the identifiers

1. **Workstream ID** — fits `workstream_id_scheme` and names an entry in `phase_vocabulary`.
2. **Sequence number** — the next unused one for that phase.
3. **Kind** — `build` when the deliverable is a change to the system, `experiment` when it is an
   answer: a measurement, a screening, a comparison. §3 and §5 change shape with it. Ask when
   unsure; getting this wrong makes the template fight the work.
4. **Slug** — kebab-case from the title. **Confirm it with the user before writing.**
5. **Parent** — the `spec_map_path` row or plan section this expands. Every spec has one.

Apply the naming rule from `check-contracts`. On a collision, stop and ask.

## Step 3 — Record the decisions first

Re-read the grilling. Every point where the user chose between real alternatives is an ADR
candidate. Test each against the bar in the `decision_records` README — hard to reverse,
surprising without context, a genuine trade-off, or an SME ruling that overturns a prior position.

**Put each candidate to the user separately and wait.** State the decision, the alternatives
considered, and why this one. An ADR asserted by an agent without a human ruling is a decision
nobody made.

Write the approved ones to `decision_records` in that directory's format, numbered from the
highest existing. Then cite them in the spec's **Anchors**. The reverse link is never written:
`grep -rl 'adr/NNNN' <spec_dir>` computes it.

## Step 4 — Triage the design before writing it

For every piece of design detail the grilling produced, ask **who needs it**, and send it to one
of exactly three destinations:

| Destination | When |
|---|---|
| **A contract** — `contracts_path`, or `glossary_path` for vocabulary | someone outside this work builds against it: a schema, an interface, an ID grammar, an output shape |
| **An ADR** — `decision_records` | it was a hard-to-reverse choice between real options |
| **Nowhere** | it is implementation: an algorithm, an internal structure, a traversal order |

There is no fourth destination, and in particular **the spec is not one.** A spec that absorbs
implementation detail grows without bound and commits to the *how* before anyone has built it,
which is the one thing spec-driven work does not ask for. Measured on a real spec, 78% of its
design section was contract and 22% was implementation that should never have been written down.

Promoting to a contract is an edit to a governing document. **Propose it, name what moves, and
wait for the user.**

## Step 5 — Write the spec

Create `spec_dir/<spec-id>/spec.md`. Read `spec_template_path` and use it verbatim; if the profile
names none, use [`references/spec-skeleton.md`](references/spec-skeleton.md). The project's
template always wins where one exists.

Frontmatter takes `spec_owner`, `spec_initial_status`, the kind, the parent, today's date read
from system context rather than guessed, and **Anchors** carrying the ADRs and contract sections
this spec stands on.

Fill §1 Why and §2 Product anchor from the conversation. Then, with the precondition met:

- **§3.** For `build`, IN / OUT / DEFERRED. For `experiment`, hypothesis, controls, and what is
  deliberately not varied.
- **§5 seams before checks.** Where does verification attach? Prefer an existing seam, take the
  highest available, use as few as possible — one is ideal. **Confirm the seams with the user
  before writing any check**, because every check inherits the choice. For `experiment`, the
  predicate leads: the measurable condition that decides whether the hypothesis held, and its
  baseline, registered before the run.

No task table. Decomposition belongs to `/tickets`, and it comes after the seams because you
cannot size a ticket until you know where it gets verified. No user stories either — the wrong
shape for work about interfaces, invariants and measurements.

## Step 6 — Register and report

Update the row in `spec_map_path` and `roadmap_path`: status, link. Then:

> **Read these two before approving: the Seams in §5, and OUT in §3.** They are where a wrong
> decision is cheapest to catch now and most expensive to discover later. If the rest of the spec
> surprises you, the grilling was too shallow.

## After approval

**`spec.md` is immutable.** Two commits in its life: created, approved. Everything that happens
afterwards is written to `acceptance.md` beside it — the compliance record at close, and any dated
amendment. An amendment cannot interleave into a blueprint it is not allowed to open, and that is
the point: a spec carrying ten amendments in its body reads as neither the agreement nor the
current truth.

Only a change to **scope, inputs and outputs, or acceptance** earns an amendment. Local divergence
found during implementation belongs in the ticket that hit it. Anything that deserves to outlive
the work goes to `decision_records`.

## Hard rules

- **Record decisions before writing the spec**, one at a time, each ruled on by the user.
- **Never pre-fill §3 or §5 without a grilling in context.** The rule was never "the agent must
  not write these" — it is that they must not be written without thought.
- **Send design to a contract, an ADR, or nowhere.** Never let the spec absorb implementation.
- **Never invent a phase or workstream ID.** Validate against `phase_vocabulary` and `spec_dir`.
- **Never duplicate an existing spec's ID or subject.** Stop and ask.
- **Never write a ticket.** That is `/tickets`, and it runs next.
- **Write scope is the spec directory, `spec_map_path`, `roadmap_path` and `decision_records`.**
  A contract edit is proposed, never made unasked.
