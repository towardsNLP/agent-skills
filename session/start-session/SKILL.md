---
name: start-session
description: Load the minimum context needed to start work. Reads generated state, checks the branch and produces a task brief. Read-only; opens no long planning document in full.
disable-model-invocation: true
---

# Start session

Read-only. This skill never writes. Diaries belong to `/end-session`, shared docs to
`/sync-progress`.

**The governing rule: the main thread never opens the progress log, diaries, plan or roadmap in
full.** Those files grow without bound. The main thread reads one short generated file. Bounded
metadata queries that return only dates or one matching row are allowed. When state is missing or
stale, a helper agent reads the long documents when the harness offers one. Otherwise use bounded
commands that return only the fields required by `templates/state.md`.

Read `planning/agent/profile.md` first. It is short, and it holds every project-specific
path and rule used below.

## Step 1 — Read your own state file

Read `planning/agent/state/<contributor>.md`, the file your own `/end-session` regenerates.
It is the whole of your starting context: active branch, active workstream, governing spec,
your last few entries as one line each, open blockers, and the next action.

**One writer per file.** Your state file is yours the way your diary is yours. No other
contributor's session writes it, so two people working in parallel never contend. There is
no shared state file that every `/end-session` rewrites; that design races.

Where the lead maintains a derived `planning/STATE.md` index across contributors, it is
written by `/sync-progress` only and is read for an overview, never as your starting context.

Stop there. Do not "also check" the progress log to be sure.

## Step 2 — Freshness check, without reading anything long

Your state file carries a `state_as_of` date. Compare it against the newest entry date in
your own diary **by reading only those dates**, not the files. Diary entries append, so the last
matching header is the newest:

```bash
state_date=$(sed -n 's/^\*\*state_as_of:\*\*[[:space:]]*//p' planning/agent/state/<contributor>.md | head -1)
diary_date=$(rg -o '^## [0-9]{4}-[0-9]{2}-[0-9]{2}' planning/diaries/<contributor>-diary.md | tail -1 | cut -d' ' -f2)
printf 'state=%s diary=%s\n' "$state_date" "$diary_date"
```

Equal or newer means it is current. Go to step 3.

Older, or the file absent, means it is stale. When helper agents are available, dispatch one with
this brief:

> Read the newest entry of `<progress_log_path>`, the newest one or two entries of
> `<diary_dir>/<contributor>-diary.md`, and the rows of `<roadmap_path>` assigned to this
> contributor. Return only the fields defined in the plugin's `templates/state.md`: active
> workstream, governing spec path, last three entries as one line each, open blockers, next
> action. Return no file contents and no quotation longer than one line.

Take the helper's fields as your context and tell the user the state file is stale so it gets
regenerated at `/end-session`. Without helper agents, use `rg`, `head` and `tail` to return only the
named dates, headings and assigned rows. Do not print whole documents into the main context.

## Step 2b — Check what other contributors have claimed

Before starting, confirm nobody else is on this workstream. The claim lives on the roadmap
row, not in a state file: a row carries its owner, and taking work means putting your name on
it **before** you start, so a parallel session skips it. Use a bounded `rg` query that returns the
matching workstream row only. For ticket work, also read that ticket's `Claimed by` field. An
unclaimed row or ticket is takeable; one claimed by someone else is not, even if it looks idle.

## Step 3 — Contributor and branch

Read `git config user.name` and match against the profile roster. No match, or no git, means
ask; never invent a contributor. Where the profile defines contexts rather than
contributors, identify the context the same way.

Run `git branch --show-current` and validate against the profile's branch convention and
trunk rules. On a trunk or shared branch, require a topic branch before any change.

## Step 4 — The governing spec, on demand and one only

Once the task is known, read the single governing `spec.md` named by state or derived from the
profile's spec path pattern. Then read `amendments.md` beside it when present. Together they are
one effective agreement. Never read a second spec "for context". No spec at all is a gap, and gets
surfaced as one.

## Step 5 — Task brief, before touching anything

```
## Task brief
Contributor or context · Branch · Phase and workstream
Goal: [one sentence]
Work kind: [build / experiment / knowledge-revision]
Governing agreement: [spec path + amendments path when present, or "none — gap"]
Evidence context: [dataset, model, ontology and artifact versions that apply, or "none"]
Constraints that apply: [from the profile and the spec]
Files likely to change / files that must not change: [profile read-only paths]
Acceptance criteria: [the spec's verification section]
Assumptions · Risks · Open questions
Explicitly out of scope: [the spec's OUT and DEFERRED]
```

Wait for confirmation. A gap the brief reveals is a blocker; surface it rather than papering
over it.

## Step 6 — Backfill check, last and cheap

Compare the last dated header in this contributor's diary, obtained with the same date query from
step 2, against
`git log --since="<date>" --author="<contributor>" --oneline`, scoped as the profile
specifies. Unlogged commits earn a backfill offer, and "skip" is an acceptable answer. This
runs last because it must never delay the start of work.

## Hard rules

- Read-only, always.
- **Never open the progress log, a diary, the plan or the roadmap in full in the main thread.**
  Use state, a helper agent, or a bounded query that returns only named metadata.
- One effective agreement, read after the task is known, never before.
- Read the governing spec before writing code. IN, OUT and DEFERRED are load-bearing.
- Flag effort drift beyond 30% over estimate, and any at-risk date the profile names.
- Flag unresolved dependencies on external reviewers or clients the profile names, as
  blockers.
- Never breach a non-negotiable constraint in the profile. If a task would, stop and surface
  it.
