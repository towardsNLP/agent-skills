---
name: sync-progress
description: Lead-only. Consolidate contributor diaries and observed work into the shared planning docs, then flag schedule drift and externally visible changes.
disable-model-invocation: true
---

# Sync progress to the shared planning docs

Reads every contributor's diary since the last sync and writes to shared docs only.
**Never writes to anyone's diary.**

Read `planning/agent/profile.md` first for the lead's identity, the diary directory, the
progress-log, plan, roadmap and contracts paths, the progress-log ordering, the workstream
vocabulary, the gate model, regeneration commands, deadlines, and
external stakeholders.

If the runner is not the lead, abort: *"/sync-progress is lead-only. Run /end-session; the
lead will sync your work on the next run."*

## Step 1 — Sync window

The newest `## YYYY-MM-DD` entry in the progress log sets the window, and all newer diary
content is in scope. With no progress log yet, everything is in scope.

## Step 2 — Read the diaries

**Glob the diary directory** rather than working from a name list, so a new contributor's
first diary is picked up automatically. Note a missing diary and carry on.

## Step 3 — Detect observed but unlogged work

Per contributor, run `git log --since="<their last diary date>" --author="<name>" --oneline`,
scoped per the profile. Record such commits tagged **(observed, unconfirmed)** for them to
confirm next session. Never infer intent beyond what the commit messages and diffs state.

## Step 4 — Update the progress log

Add a dated entry, or extend the same-day one, at the position `progress_log_ordering`
specifies. Existing entries are never deleted or rewritten.

```markdown
## YYYY-MM-DD — [Title] (Workstreams: <ids>)

### Context
### <Contributor name>          one section per contributor with work in the window
### Files created / modified
### Decisions made
### Blockers / risks
### Milestone or gate progress  per the profile's gate model
### Next priorities             numbered, referencing workstream or spec IDs
---
```

With one contributor, simplify to that section.

## Step 5 — Update the roadmap

Move *not started* to *in progress* when work begins. Move *in progress* to *done* only when
the spec's exit criterion **and** any gate the profile defines are met, not merely when code
is written. Use *blocked on `<reason>`* when a diary surfaces one. Don't fabricate status;
"started but not finished" is recorded as exactly that.

For experiments, distinguish `run completed` from `predicate supported`. Preserve
`INCONCLUSIVE` and link the experiment record. For knowledge revisions, distinguish `model
changed` from `authority approved` and link the competency-query, constraint and provenance
evidence. Never turn missing evidence into a positive or negative claim.

## Step 6 — Update the master plan's current-state section

Only when a workstream completed or started, a gate closed, or a phase boundary was crossed.
Otherwise leave it alone.

## Step 7 — Update the conventions file, on gated triggers only

Only when the diaries verify one of: a new module or top-level directory; a new convention
all future work must follow; an added or changed environment variable or config; an
architecture change everyone needs to know; or a phase or gate status change. Add any
project-specific trigger the profile names. If none apply, don't touch it. Most syncs won't.

## Step 8 — Update the contracts file, rarely

A deliberate, recorded contract change means update it and note the change in this sync
entry. A contract *violation* means do not update. Surface it as a sync blocker. No-op when
the profile names no contracts file.

## Step 9 — Regenerate the shared state index

Rewrite `planning/STATE.md` whole: a derived index over the per-contributor state files and
this sync entry. Set `state_as_of` to the date of the entry you just wrote. Under 400 words,
links rather than quotes, oldest cut first.

**This skill is the only writer of `planning/STATE.md`**, which is what keeps it free of
contention. It is an index, not a store: one line per thread pointing at where the detail
lives, never a restatement of it. Because it is derived, a merge conflict on it is resolved
by regenerating, never by hand-merging.

Never write a contributor's own `planning/agent/state/<name>.md`. Those belong to them, like
their diaries.

## Step 10 — Auto-memory and regenerated surfaces

Write stable patterns and status changes to this project's agent memory, whose location the
harness provides. Run any regeneration commands the profile lists; their diffs are part of the
sync commit.

## Step 11 — Flag drift and externally visible changes

Emit a clear **schedule alert** when a milestone or deadline named in the profile is at risk,
when a workstream is more than 30% over estimate or has been in progress for more than twice
its estimate with nothing done, when there are cross-contributor blockers, or when an
external dependency is slipping with no new date. Separately, flag work that warrants an
update to an external reviewer or client the profile names.

## Idempotency

Read each shared doc before modifying it. Never remove a progress-log entry. A second run on
the same day is close to a no-op for work already captured. Diaries are the source of truth,
so don't embellish.

## What this skill does not do

- It does not write to any diary, modify specs, or touch a path the profile marks read-only.
- It does not fix convention violations. It surfaces them as a sync blocker.
- It does not communicate with any external stakeholder. Those channels stay manual.
