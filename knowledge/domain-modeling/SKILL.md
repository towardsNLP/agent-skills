---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing project terminology, writing or editing the glossary, or recording a decision record. Resolves its targets from planning/agent/profile.md rather than assuming CONTEXT.md.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* the glossary for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## Where the glossary and the decisions live

**Resolve the targets before writing anything.** Most real projects already have a glossary and a
place for decisions, under their own names. Writing to `CONTEXT.md` beside an existing glossary
creates a second owner for one question, which is how two definitions of the same term end up in
one repo.

Read `planning/agent/profile.md` and use, in this order:

1. `glossary_path` — the project's canonical vocabulary.
2. `contracts_path` — a naming constitution counts as the glossary when there is no separate one.
3. `modeling_handbook_path` — if it governs how the domain is modelled, its rules bind this
   session even when the terms live elsewhere.
4. Only if the profile names none of these, and the repo has no glossary of any kind, create
   `CONTEXT.md` at the root, lazily, when the first term is resolved.

For decisions: `decision_records` from the profile, else an existing `docs/adr/`, else create
`docs/adr/` lazily when the first one is needed.

**Never create a second glossary.** If you cannot tell which file is canonical, ask; do not start
one. Where the project's glossary has its own format, follow it rather than
[CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) — that file is the fallback shape, not the standard.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the resolved glossary, call it out immediately.
"Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update the glossary inline

When a term is resolved, write it to the resolved glossary right there. Don't batch these up:
capture them as they happen, in whatever format that file already uses.

A glossary is a glossary and nothing else: no implementation detail, no spec content, no scratch
notes.

### Respect the project's provenance rules

Where the profile names a `modeling_handbook_path` or the glossary carries provenance fields
(source, confirmed-by, rationale), a term you resolve in conversation is **not** confirmed
knowledge. Record it at the tier the project uses for an unconfirmed claim, and say so. Never
promote a term to confirmed because it was settled with the agent rather than with the expert who
owns it.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
