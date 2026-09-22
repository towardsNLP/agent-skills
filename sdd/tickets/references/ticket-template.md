# Ticket template

One ticket per file at `ticket_dir/<spec-id>/NN-slug.md`.

```markdown
# NN — <title>

**What becomes true:** what is the case once this lands. One or two sentences, stated as an
outcome rather than a layer-by-layer implementation list.

**Blocked by:** NN, NN — or `none (can start immediately)`
**Governs:** the contract sections and ADRs this must respect
**check_type:** test | gate | sme | manual
**check:** `pytest tests/unit/test_loader.py::test_rejects_unknown_predicate`
**Claimed by:** unclaimed

## Approach (non-binding, ≤150 words)

- What the author had in mind when cutting this ticket.
- The implementer may depart from it without an amendment and without asking.
- Six bullets at most. This is a hint, not a requirement.

## Outcome

<!-- Written once, by the implementing session at close. Empty until then. -->

**PR:** #NN
**Diverged:** what differed from the blueprint, or `nothing`.
```

## The fields, and why each is there

**What becomes true** rather than "what to build": it survives work with no user-facing surface,
which is most knowledge-engineering and experiment work.

**Blocked by** makes the set a graph rather than a list, so anyone can pick up a ticket on the
frontier without asking what is safe to start.

**Governs** is how a fresh session inherits the constraints without reading the whole constitution.

**check_type** and **check** are the acceptance criteria. There is no checkbox list, because
checkboxes measurably do not get ticked: across three repositories, 95 acceptance boxes were
written into specs and **not one was ever ticked**. Several criteria become several assertions
inside one named check, not several boxes — a box and a test that can disagree is a second source
of truth, and the box is the one that lies.

**Claimed by** is the one status a human writes, because it is the one a script cannot compute.
Doneness is always derived by running the check. Unclaimed means ready.

**Approach** is capped because the thinking from the grilling is real and discarding it is waste,
but writing it as prescription is how a spec reached 811 lines of design that nobody was allowed
to depart from.

**Outcome** is what the implementing session writes instead of a status: the PR, and what diverged.
This is the ticket's most durable content and the reason the file stays where it is after close —
never moved to a `done/` folder, never deleted.
