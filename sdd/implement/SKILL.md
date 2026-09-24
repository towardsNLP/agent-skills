---
name: implement
description: Execute one ticket in a fresh session. Claims it, selects the build, experiment or knowledge-revision proof loop from the spec, runs the named check, and records the outcome. Demonstrates done rather than declaring it.
disable-model-invocation: true
---

# Implement

One ticket, one session. Open the bracket by claiming it, close it by recording what happened.

Read `planning/agent/profile.md` for `ticket_dir`, `spec_dir`, `contracts_path`,
`ticket_status_command`, `branch_convention`, `sme_register_path` and the optional research or
knowledge paths used by this ticket's work kind.

## Step 1 — Claim it

Read the ticket. If `Claimed by` names someone else, stop and say so — that is what the field is
for. Otherwise set it to your name and branch, per `branch_convention`, and commit that line
before writing any code. **A state file records where you are; only a claim stops two people
taking the same work.**

## Step 2 — Load exactly what the ticket names

The ticket, its spec at `spec_dir/<spec-id>/spec.md`, `amendments.md` beside it when present, and
the contract sections under **Governs**. Apply amendments in date order. Nothing else. That list
is deliberate: a ticket is self-contained so a fresh session can execute it without reading the
other tickets or the whole constitution.

Read the `Approach` note as a hint. **You may depart from it without an amendment and without
asking** — it records what the author had in mind, not what you owe.

## Step 3 — Confirm the blockers have landed

Run the check of every ticket in **Blocked by**. A blocker whose check fails is a blocker that has
not landed, whatever its Outcome section says. Stop and report rather than building on it.

## Step 4 — Run the proof loop selected by the spec

Work at the **seam the spec already chose** in section 5. Moving it invalidates every check that
hangs off it. If the seam is wrong, stop and report a spec finding.

### `build`

Use `/tdd`. Write the missing check first, watch it fail, add the smallest behaviour that makes it
pass, then refactor while it stays green. Typecheck and run the focused test often. Run the full
suite once at the end.

### `experiment`

Confirm the hypothesis, baseline, predicate, dataset or sample version, split policy, metric and
randomness policy were registered before the run. A missing item is a design gap, not something to
choose after seeing results. Validate the input and leakage checks first, run the planned arm, and
write the artifact with its parameters and versions. Report the predicate as supported, not
supported or `INCONCLUSIVE`. A successful command proves that the run completed. Only the
registered predicate determines what the project may claim.

### `knowledge-revision`

Run the competency query or constraint first and capture the failing result. Revise the governed
model, rule or representation, preserving its source and approval provenance. Re-run the query,
shape constraint and expected-entailment regressions. State the inference boundary. Absence is
`unknown` unless the governing contract explicitly closes the world for that question.

## Step 5 — Run the ticket's check

Run the `check` exactly as written. `gate`, `metric`, `dataset`, `query` and `artifact` checks are
commands whose exit code carries their named condition. For `check_type: sme`, confirm the named
row in `sme_register_path` has resolved — an unresolved row is not done, however finished the work
looks. For `manual`, follow the procedure and report the result.

A check that will not resolve — a moved test path, a renamed command — is a defect in the ticket.
Fix the ticket's `check` field and say that you did.

## Step 6 — Close the ticket

Fill in **Outcome**: the PR number or other durable change identifier, and what diverged from the
blueprint, or `nothing`. Set
`Claimed by` back to `unclaimed` only if the work is abandoned; a closed ticket keeps the name of
whoever did it.

**Never write a status.** You demonstrate done by leaving a check that passes, not by declaring
it. The one thing you write is the thing a script cannot compute: *why it differed.*

The file stays exactly where it is. It is not moved to `done/` or deleted. The durable change
identifier points at that path, and the divergence record is the ticket's most durable content.

## Step 7 — If this was the last ticket, close the spec

When every ticket for the spec has an Outcome, write `spec_dir/<spec-id>/acceptance.md`: one
compliance line per requirement in the effective agreement, which is `spec.md` followed by
`amendments.md` in date order. Use PASS / MODIFIED / PARTIAL / SKIPPED / FAIL, with a reason for
anything that is not PASS.

Where implementation diverged from a requirement, **say so here with MODIFIED rather than editing
the requirement it diverged from.** `spec.md` is frozen; it records what was agreed, and this file
records what happened. Only a change to scope, inputs and outputs, or acceptance becomes a dated
amendment. `/adr-spec` records that change in `amendments.md`; this skill never writes it.

## Step 8 — Review and hand off

Run `ticket_status_command` and report what it says. Then review the work — `/code-review` where
the project has it — and commit to the claimed branch.

## Hard rules

- **Never edit `spec.md`.** Divergence goes in the ticket's Outcome; a contract change is proposed
  to the user and made by them.
- **Never edit `amendments.md`.** Read it after the spec. `/adr-spec` is its only writer.
- **Never edit another ticket.** If this work changes what a later ticket should be, say so — the
  fix is to re-run `/tickets`, not to patch one by hand.
- **Never take a ticket claimed by someone else.**
- **Never move the seam.** If the spec's seam is wrong, that is a finding to report, not a choice
  to make mid-build.
- **One ticket per session.** The ticket was sized to a fresh context window; taking two spends
  the budget that sizing bought.
