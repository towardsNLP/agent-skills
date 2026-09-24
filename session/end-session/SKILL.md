---
name: end-session
description: Log the session to the contributor's own diary. Writes one file only; shared docs belong to sync-progress.
disable-model-invocation: true
---

# End session

Log what was accomplished. This writes this contributor's own diary, regenerates
its own state file, and for the lead updates the project's agent memory. Everyone runs it.

Read `planning/agent/profile.md` first for the roster, the diary directory and filename
pattern, the diary header text, the workstream vocabulary, read-only paths, and whether the project runs a separate `/sync-progress`.

> **Merged mode.** If the profile sets `has_sync_progress: false`, as solo projects do, this
> skill also performs the shared-doc updates in the same pass, following `/sync-progress`'s
> steps and rules.

## Step 0 — Identify the contributor

Match `git config user.name` and `user.email` against the profile roster. No match means
ask. **Never write to another contributor's diary**; diaries are personal context. A diary
that does not exist yet is created on first run using the profile's header text.

## Step 1 — Gather the session summary

```bash
git branch --show-current
git status --short
git diff --stat
git log --oneline --since="<session start>"
```

An active task list is signal too. **Never invent work.** Log only what git verifies or the
contributor dictates. With no git, summarise from the session's actual file changes.

## Step 2 — Append a dated entry

Required: goal, what I did, branch or context, workstream tag. Optional, and omitted when empty:
evidence produced, observations, interpretations or decisions, epistemic risks, blockers, next
session. For experiment and knowledge work, keep observations separate from interpretations.

```markdown
## YYYY-MM-DD — [Brief session title]

**Branch:** `<branch-name>`
**Workstream:** <per the profile's ID scheme>

### Goal
[1–2 sentences]

### What I did
- [Concrete deliverables, with file paths and counts]

### Evidence produced
### Observations
### Interpretations / decisions
### Epistemic risks
### Blockers
### Next session

---
```

Don't pad empty sections. Friction matters more than form here.

## Step 3 — Regenerate your own state file

Rewrite `planning/agent/state/<contributor>.md` whole, to the shape in the plugin's
`templates/state.md`. Set `state_as_of` to the date of the entry you just wrote. Keep it
under 300 words, link rather than quote, and cut oldest first.

Record the ticket path and exact context anchors along with the work kind, active hypothesis or
competency question, evidence versions and last verified command when they apply. Prefer the
ticket's `Governs` field over restating anchors in state. "The run completed" is an observation.
A hypothesis result is a separate statement tied to its registered predicate.

**Write only your own file**, the same rule as diaries. Never write another contributor's
state file, and never write a shared one. One writer per file is what lets parallel sessions
run without contending; a single shared state file that every `/end-session` rewrites races.

This is not optional bookkeeping. Your state file is the only thing your `/start-session`
reads, so a skipped regeneration means the next session either starts stale or pays for a helper
agent or bounded reconstruction.

## Step 4 — Auto-memory, lead only

If the contributor is the lead named in the profile, update this project's agent memory with
**stable** patterns, conventions and insights confirmed this session. Persistent facts, not
session state. Refine existing entries rather than duplicating them. Everyone else skips this
step.

The harness tells you where its own memory lives. Do not read a path for it out of the profile,
and never write one in: agent memory is per-user and machine-local, so a path committed to a repo
is wrong for every contributor except the one who wrote it.

## What this skill does not do

- It does not update the progress log, master plan, roadmap or conventions file. That is
  `/sync-progress`.
- It does not touch another contributor's diary or state file, and it never writes a shared
  state file.
- It does not modify specs, which belong to their workstream owner, or any path the profile
  marks read-only.

## Rules

- Read the diary before appending. **Append only** — never overwrite or remove an entry.
- The branch or context and the workstream tag are required; `/sync-progress` depends on the
  tag.
- Be specific about paths and counts. "Improved X" wastes future-you's time.
- Verify claims with `git status` and `git diff --stat` before writing them.
- Say plainly when a task is only partly done, so someone can pick it up.
- One session, one entry. Extend a same-day entry rather than adding a second.
- Honour any confidentiality or draft-handling rule the profile names for external-facing
  text.
