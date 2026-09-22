---
name: deconstruct
description: Break a whole project into the set of specs it needs. Maps needs and components to spec IDs with their dependency edges, and writes the planned set to a spec map. Run rarely, at project level, before any spec exists.
disable-model-invocation: true
---

# Deconstruct

Move from a problem too big to spec to a **set of specs that covers it.** This runs at project
level and it runs rarely — at the start, and again when the shape of the work genuinely changes.

Read `planning/agent/profile.md` for `plan_path`, `roadmap_path`, `spec_map_path`, `spec_dir`,
`glossary_path`, `contracts_path`, `workstream_id_scheme` and `phase_vocabulary`.

## Step 1 — Check the vocabulary exists first

**You cannot spec what you cannot name.** Read `glossary_path` — or `contracts_path` where the
project has no separate glossary — and list every term this project turns on.

Where a term is missing, ambiguous, or used two ways in the plan, **say so and stop short of
inventing one.** Naming is `domain-modeling`'s job and it is upstream of this skill. Report the
gaps, let the user close them, and resume. A component set built on unsettled vocabulary
decomposes along the wrong lines and every spec below it inherits the error.

## Step 2 — Read the whole problem

`plan_path`, `roadmap_path`, any contract or requirements document the profile names, and enough
of the code to know what already exists. This is the one skill that reads broadly on purpose;
everything downstream reads narrowly.

## Step 3 — Enumerate the components

A component is **a thing that can be specified independently and verified on its own.** Work from
two directions and reconcile:

- **Needs** — what someone must be able to do, or what question must be answered.
- **Structure** — what the system is made of, and what already exists in the code.

A need with no component is unbuilt scope. A component serving no need is a candidate to cut —
raise it rather than quietly keeping it.

Give each an ID that fits `workstream_id_scheme` and names an entry in `phase_vocabulary`.

## Step 4 — Draw the edges

For each component, what must exist before it can be specified or built. Foundations before the
things that stand on them. Flag any cycle: a cycle means the boundary is in the wrong place, and
it is cheapest to move now.

## Step 5 — Put the map to the user

Present the components with their IDs, what each covers, and its blockers. Ask:

- Is anything missing — a need with no component?
- Is anything here that should be cut?
- Are the boundaries in the right places, and is the granularity right?

Iterate until approved. Write nothing before that.

## Step 6 — Write the planned set, and only the planned set

Write `spec_map_path` to the shape in
[`references/spec-map-skeleton.md`](references/spec-map-skeleton.md).

**Record what is planned. Never record what exists.** Which specs are written, which have tickets,
which are done — all of that is computed by `ticket_status_command` from the filesystem. This split
is not tidiness. A hand-maintained catalogue of project state has already failed in practice: one
recorded, in its own header, the exact failure it was built to prevent — a spec's task needed two
other specs and neither had been written — because keeping it current was someone's job and that
someone was busy. The planned set changes when a human decides it does. Everything else is derived.

Report the component count, the ones with no blockers, and the vocabulary gaps still open.

## Hard rules

- **Never author a glossary term.** Flag the gap and hand it to `domain-modeling`.
- **Never write a spec or an ADR.** This skill produces the map; `/adr-spec` walks it, one row at
  a time.
- **Never record status, counts or progress in the map.** Those are derived, and a written copy
  will disagree with the filesystem within a fortnight.
- **Write scope is `spec_map_path` only.** Changes to `plan_path` or `roadmap_path` are proposed,
  never made.
