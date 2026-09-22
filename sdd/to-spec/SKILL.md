---
name: to-spec
description: Create a spec, and fill it from the conversation that earned it. Validates the ID, registers it in the roadmap, and refuses to write the sections that need deliberate thought unless a grilling session preceded it.
disable-model-invocation: true
---

# To spec

One skill for both halves of authoring a spec: the shell, with a validated ID and a roadmap row,
and the content, synthesized from the conversation already in context.

Read `planning/agent/profile.md` for `spec_dir`, `spec_path_pattern`, `spec_template_path`,
`spec_owner`, `spec_initial_status`, `workstream_id_scheme`, `phase_vocabulary`, `roadmap_path`,
`plan_path` and `decision_records`.

## The precondition

**Do not write §3 Scope, §5 Task breakdown or §6 Verification unless a grilling session preceded
this in the same context.** Those three carry the thinking; pre-filled, they get approved without
being read, which is worse than empty.

No grilling in context means create the shell, fill §1 and §2 from what the conversation supports,
leave the rest as template placeholders, and say: *"§3, §5 and §6 are unfilled. Run `/grill-me`
and re-run this, or fill them by hand."* Do not interview the user here; that is grilling's job
and it does it better.

Keep grilling, this skill, and `/to-tickets` in **one unbroken context window**. Don't compact
between them.

## Step 1 — Check nobody has already specified this

Before drafting, grep `spec_dir` for a spec covering the same subject and check `roadmap_path`
for a row already claimed. A duplicate ID is refused by `check-contracts`; a duplicate *subject*
under a fresh ID is not, and is the more expensive mistake. If one exists, stop and say so: the
choice to supersede or extend is the user's.

## Step 2 — Settle the identifiers

1. **Workstream ID** — must fit `workstream_id_scheme` and name an entry in `phase_vocabulary`.
   If unstated, read `roadmap_path` and ask.
2. **Sequence number** — the next unused one for that phase in `spec_dir`.
3. **Kind** — `build` or `experiment`. A spec whose deliverable is a change to the system is
   `build`. One whose deliverable is an answer — a measurement, a screening, a comparison — is
   `experiment`, and §3 and §6 change shape accordingly. When unsure, ask; getting this wrong
   makes the template fight the work.
4. **Slug** — kebab-case from the title. **Confirm it with the user before writing.**
5. **Anchors** — the decision records under `decision_records` this spec respects, plus the
   strategy docs and prior specs it depends on. **Cite the decision records by path**: they are
   the reason parts of the design are not open for rediscussion.

Apply the naming rule from `check-contracts`: the path matches `spec_path_pattern`, the slug is
lowercase kebab-case, and the ID does not already exist. On a collision, stop and ask.

## Step 3 — Write the shell

Read `spec_template_path` and use it verbatim. If the profile names none, use the skeleton in
[`references/spec-skeleton.md`](references/spec-skeleton.md) — the project's template always wins
where one exists.

Frontmatter takes `spec_owner`, `spec_initial_status`, the kind, and today's date read from
system context rather than guessed.

## Step 4 — Fill what the conversation earned

§1 Why and §2 Product anchor from the conversation. Then, **only with the precondition met**:

- **§3.** For `build`, IN / OUT / DEFERRED. For `experiment`, hypothesis, controls, and what is
  deliberately not varied. OUT is one of the two sections worth the user's close attention.
- **§6 Seams first, before any check.** Where does verification attach? Prefer an existing seam,
  take the highest available, use as few as possible. For a rule encode that is usually the
  acceptance corpus; for a knowledge layer, the validator; for an experiment, the yardstick.
  **Confirm the seams with the user before writing the checks**, because every check below them
  inherits the choice. For `experiment`, the predicate comes first: the measurable condition that
  decides whether the hypothesis held, with its baseline.
- **§5.** Tasks, each ending in a verifiable state, each with its **Blocked by** edges. A task
  with no blockers is takeable now. Leave `/to-tickets` to expand them into briefs.

No user-stories section. This template does not have one, and stories are the wrong shape for
work that is really about interfaces, invariants and measurements.

## Step 5 — Register and report

Add or update the row in `roadmap_path`: initial status, link to the file. If the workstream row
is new, say so — it may need a sanity check against `plan_path`.

Report the files written, then:

> **Read these two before approving: the Seams in §6, and OUT in §3.** They are where a wrong
> decision is cheapest to catch now and most expensive to discover later. If the rest of the spec
> surprises you, the grilling was too shallow.

## After approval

**The spec is frozen.** It is a snapshot of what was known when it was approved, and it is not
maintained afterwards. Scope changes land as a dated amendment block, never a silent edit. §6's
compliance table is filled in once at close, as the acceptance record.

Anything implementation teaches that deserves to outlive the work goes to `decision_records`, not
into an edited spec.

## Hard rules

- **Never pre-fill §3, §5 or §6 without a grilling in context.** The rule was never "the agent
  must not write these" — it is that they must not be written without thought.
- **Never invent a phase or workstream ID.** Validate against `phase_vocabulary` and `spec_dir`.
- **Never duplicate an existing spec ID, or an existing spec's subject.** Stop and ask.
- **Never skip slug confirmation.** Bad slugs propagate into branch names, test names and paths.
- **Write scope is `spec_dir` and `roadmap_path` only.** Never `plan_path`, never a governing
  document.
