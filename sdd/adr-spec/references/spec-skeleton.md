# Spec skeleton

The fallback shape, used only when the profile names no `spec_template_path`. **A project's own
template always wins where one exists** — it carries that project's phase vocabulary, ID scheme
and compliance codes, which this cannot.

Three files may exist per spec. `spec.md` is frozen at approval. `amendments.md` holds approved
changes to the agreement. `acceptance.md` records what happened at close.

## `planning/specs/<spec-id>/spec.md`

```markdown
# Spec <ID> — <Title>

| | |
|---|---|
| **Kind** | build / experiment / knowledge-revision |
| **Workstream** | <ID> — <short name> |
| **Parent** | <the spec-map row or plan section this expands> |
| **Owner** | <from profile> |
| **Status** | <initial status from profile> |
| **Created** | YYYY-MM-DD |
| **Anchors** | <ADRs respected, contract sections relied on, prior specs> |

## 1. Why
The gap this closes, in a paragraph. What is wrong or missing today.

## 2. Product anchor
Who this is for and what changes for them. Not implementation.

## 3. Scope
**build** — three lists:
- **IN**: what this spec covers.
- **OUT**: explicitly not covered. Read this one closely.
- **DEFERRED**: recognised, pushed to a later spec, with the reason.

**experiment** — replaced by:
- **Hypothesis**: the claim, stated so a result can contradict it.
- **Controls**: what is held constant, and what is deliberately varied.
- **Not varied**: dimensions left alone on purpose, and why. The experiment's OUT.

**knowledge-revision** — replaced by:
- **Competency questions**: the questions the model or rule set must answer.
- **Authority**: the source, SME ruling or governing model being revised.
- **Inference boundary**: what may be derived, under which assumptions.
- **Unknown / excluded**: what remains unresolved or outside the represented world.

## 4. Inputs and outputs
What goes in, what comes out, and any side effects. Interfaces, not algorithms.

## 5. Seams and acceptance
### Seams
Where verification attaches, decided before any check is written. Prefer an existing seam, take
the highest available, use as few as possible — one is ideal.

For an **experiment** the predicate leads: the measurable condition that decides whether the
hypothesis held, its baseline, and how it will be measured. Registered before the run.

For a **knowledge revision**, competency queries lead. Name the constraint checks, expected
entailments, provenance requirements and any open-world or closed-world assumption needed to
interpret absence.

### Automated checks
**V1** — description — command — expected outcome.

### Manual checks
**M1** — description — steps — expected outcome.

## 6. Risks
What could make this wrong, late or unusable, and what would show it early.

## 7. References
Paths to the documents, data and code this depends on.
```

## `planning/specs/<spec-id>/amendments.md`

```markdown
# Amendments — Spec <ID>

Append only, newest last. `/adr-spec` writes one entry per approved change to scope, inputs and
outputs, or acceptance. Read after `spec.md`; later entries supersede earlier ones only where they
say so.

### YYYY-MM-DD — <what changed>
**Approved by:** <person or recorded authority>
**Anchors:** <ADRs, contract sections, SME rulings or evidence that govern this change>
**Section:** §N
**Change:** what the spec now promises instead.
**Why:** what was learned, and where it came from — a ticket, an ADR, an SME ruling.
```

## `planning/specs/<spec-id>/acceptance.md`

```markdown
# Acceptance — Spec <ID>

Written once, at close. It evaluates the effective agreement: `spec.md` followed by
`amendments.md` in date order.

## Compliance
Filled in once, at close.

**S1** — spec_ref — requirement verbatim — PASS / MODIFIED / PARTIAL / SKIPPED / FAIL — notes.
```

## Why these seven, and no eighth

§1 and §2 say why the work exists and for whom, so a reader can judge whether it should.
§3 bounds it, and OUT is where scope creep is cheapest to stop.
§4 fixes the interface.
§5 makes it checkable, and the seams decide where — which is also what makes a ticket sizeable.
§6 says what could go wrong while there is still time.
§7 makes it traceable.

**There is no task section.** Decomposition is `/tickets`, and `ls planning/tickets/<spec-id>/` is
the index — a table restating it would be a second source of truth that can disagree with the
first. **There are no user stories.** Wrong shape for work about interfaces, invariants and
measurements.

Drop a section only when it is genuinely empty, and say so rather than deleting it silently.
