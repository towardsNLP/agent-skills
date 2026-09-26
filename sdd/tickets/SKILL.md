---
name: tickets
description: Cut an approved spec into tickets — tracking records, one per unit of work, each independently verifiable by a named check and sized to one fresh session. Never edits the spec.
disable-model-invocation: true
---

# Tickets

A **ticket is a tracking record used to manage the work**, not a design document. It says what
becomes true, what gates it, what proves it done, and who has it. The design lives in the spec and
the contracts; the implementation is discovered while building.

Read `planning/agent/profile.md` for `spec_dir`, `spec_path_pattern`, `ticket_dir`, `contracts_path`, `sme_register_path`
and `ticket_status_command`.

Runs straight after `/adr-spec`, in the same context window: the seams are settled, and **you
cannot size a ticket until you know where it gets verified.**

## Step 1 — Load one spec, and only one

Read the spec at the path **`spec_path_pattern` declares** — never assume
`spec_dir/<spec-id>/spec.md` — then `amendments.md` in the same directory when it exists, then
the contract sections its Anchors cite. Nothing else. The effective agreement is the frozen spec
followed by approved amendments in date order. If it has no Seams section filled in, stop: there
is nothing to size against.

## Step 2 — Read the current state of the code

Use the project's vocabulary in titles and descriptions, and respect the ADRs the spec anchors.
Look for **prefactoring** opportunities — *make the change easy, then make the easy change.* Any
prefactoring becomes its own ticket, and it goes first.

## Step 3 — Cut the tickets

**Each ticket is independently verifiable, and the check is what makes it so.** Verticality is not
required. Cutting a complete path through every layer is how you get independent verifiability
*when the deliverable has a user-facing surface*; a schema definition, a knowledge layer or an
experiment arm has none, and forcing one produces a fake. The named check is the mechanism.

**Size each ticket to one fresh context window.** That bound is what makes "implement each ticket
in its own session" true rather than aspirational.

Give each ticket its **blocking edges** — the tickets that must land before it can start. A ticket
with no blockers is takeable now, and work proceeds on the **frontier**: any ticket whose blockers
are all done.

Pick a `check_type` for each:

| `check_type` | The check is | Derived by the status script |
|---|---|---|
| `test` | a test node id alone — `path::name`, no runner | runs it with `test_command` |
| `gate` | a command with a pass condition — a corpus, a validator, an experiment predicate | runs it |
| `metric` | a command that compares a named metric with its registered baseline or threshold | runs it |
| `dataset` | a command that validates schema, grain, identifiers, lineage or split integrity | runs it |
| `query` | a command that runs a competency, SQL, SPARQL or graph-regression query | runs it |
| `artifact` | a command that validates an output manifest, structure, hash or provenance | runs it |
| `sme` | a row in `sme_register_path` that must resolve | greps it |
| `manual` | a human procedure | reported as unknown, always |

A ticket whose check you cannot name is a ticket you have not finished cutting. Say so rather than
inventing one.

Use the spec's work kind to choose what the ticket proves:

- `build`: behaviour through `test` or a system `gate`.
- `experiment`: registered predicates and evidence through `metric`, `dataset` or `artifact`.
  A completed run may still produce `INCONCLUSIVE`; the ticket proves the run and record, not the
  preferred hypothesis.
- `knowledge-revision`: competency questions, constraints and provenance through `query`,
  `dataset`, `artifact` or `sme`.

### Wide refactors are the exception

A **wide refactor** is one mechanical change — rename a column, retype a shared symbol, change an
ID grammar across a corpus — whose **blast radius** fans across everything at once, so no single
ticket can land green. Do not force it into one. Sequence it as **expand–contract**:

1. **Expand** — add the new form beside the old so nothing breaks.
2. **Migrate** — move call sites in batches sized by blast radius, one ticket per batch, each
   blocked by the expand. The old form still exists, so every batch stays green.
3. **Contract** — delete the old form, in a ticket blocked by every migrate batch.

Where even the batches cannot stay green alone, keep the sequence and let them share an
integration branch that all block a final integrate-and-verify ticket. Green is promised only
there, and the tickets say so.

## Step 4 — Put the breakdown to the user

Present a numbered list: title, blocked by, what becomes true, and the check. Then ask:

- Is the granularity right — too coarse, too fine?
- Does each ticket depend only on tickets that genuinely gate it?
- Should any be merged or split?

Iterate until the user approves. Write nothing before that.

## Step 5 — Write them

One file per ticket at `ticket_dir/<spec-id>/NN-slug.md`, numbered from `01` in dependency order,
blockers first. Use [`references/ticket-template.md`](references/ticket-template.md). One ticket
per file, never a combined one.

Report the count, the frontier — which tickets are takeable now — and the path.

## Re-ticketing is normal

Re-run this on a spec that already has tickets whenever the work teaches you the cut was wrong.
Experiment specs need it by nature: you cannot write the ablation's ticket until the first arm has
run. **Add and renumber the open tickets; never touch one that carries an Outcome.** A closed
ticket is a record of what happened, and the reason the spec did not have to be reopened.

## Hard rules

- **Never edit the spec or its amendments.** The agreement is frozen or append-only, and this
  skill is what makes that mechanical rather than aspirational. If it is wrong, say so and stop.
- **Never edit a ticket that has an Outcome.**
- **Exactly one path per ticket: the check.** No other file paths, no line numbers. A path with a
  test behind it fails loudly when it moves; an incidental one rots in silence.
- **No code snippets**, with one exception: a snippet that encodes a decision more precisely than
  prose can — a schema, a state machine, a type shape. Trim it to the decision, not a working
  demo.
- **Never write a status.** Doneness is derived from the check. The only status a human writes is
  the claim.
- **Keep `Approach` under 150 words.** The cap is the mechanism; without it the ticket grows back
  into a design document.
