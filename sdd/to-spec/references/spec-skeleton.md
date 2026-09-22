# Spec skeleton

The fallback shape, used only when the profile names no `spec_template_path`. **A project's own
template always wins where one exists** — it carries that project's phase vocabulary, ID scheme
and compliance codes, which this cannot.

```markdown
# Spec <ID> — <Title>

| | |
|---|---|
| **Kind** | build / experiment |
| **Workstream** | <ID> — <short name> |
| **Owner** | <from profile> |
| **Status** | <initial status from profile> |
| **Created** | YYYY-MM-DD |
| **Effort estimate** | TBD |
| **Anchors** | <decision records respected, prior specs, source documents> |

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

## 4. Inputs and outputs
What goes in, what comes out, and any side effects.

## 5. Task breakdown
Each task ends in a verifiable state. Blocked by names what must land first, or `—` for takeable now.

| # | Task | Blocked by | Owner | Hours |
|---|---|---|---|---|

## 6. Verification
### Seams
Where verification attaches. Prefer existing, take the highest, use as few as possible.
For an experiment the predicate comes first: the measurable condition that decides the hypothesis,
and its baseline.

### Automated checks
**V1** — description — command — expected outcome.

### Manual checks
**M1** — description — steps — expected outcome.

### Spec-compliance checks
Filled in once at close, as the acceptance record.
**S1** — spec_ref — requirement verbatim — PASS / MODIFIED / PARTIAL / SKIPPED / FAIL — notes.

## 7. References
Paths to the documents, data and code this depends on.
```

## Why these seven

§1 and §2 say why the work exists and for whom, so a reader can judge whether it should.
§3 bounds it, and its OUT list is where scope creep is cheapest to stop.
§4 fixes the interface.
§5 makes it executable, and the blocking edges make it parallelisable.
§6 makes it checkable, and the seams decide where.
§7 makes it traceable.

Drop a section only when it is genuinely empty, and say that it is rather than deleting it
silently.
