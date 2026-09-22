---
name: wrap-day
description: Lead-only sequencer that runs end-session then sync-progress, aborting on failure so a day is never half-wrapped.
disable-model-invocation: true
---

# Wrap day

Runs `/end-session` and then `/sync-progress`, in that order, for a lead who both did
session work and wants it consolidated now. This is purely a sequencer. It adds ordering,
abort-on-failure and a recovery message, and nothing else.

Read `planning/agent/profile.md` for `lead`, `diary_dir` and `progress_log_path`.

## Workflow

1. **Gate on the lead.** Check the runner, normally `git config user.name`, against `lead`.
   On a mismatch, abort before any write: *"/wrap-day is lead-only because it calls
   /sync-progress. Run /end-session to log your diary; the lead will sync your work on the
   next run."* Do not quietly fall back to `/end-session` alone. That reintroduces the role
   ambiguity the two-skill split exists to remove.
2. **Run `/end-session`** exactly as if it were called directly, with all its rules. If it
   errors or is interrupted, abort the sequence. Never sync a half-written entry.
3. **Run `/sync-progress`** with all its rules. If it fails partway, surface: *"Diary entry
   written; sync failed at step N. Re-run /sync-progress after fixing."*
4. **Summarise**: the diary file written, the files sync updated, and any alerts sync raised.

This is not atomic. If step 2 succeeds and step 3 fails, the diary entry is already on disk.
That is a recoverable partial, fixed by re-running `/sync-progress` on its own.

## When not to use it

- Session work now, sync later: `/end-session` only.
- No session work, but other people's diaries need consolidating: `/sync-progress` only.
- Several sessions in one day: `/end-session` per session, `/sync-progress` once. Not
  `/wrap-day` repeatedly, which creates duplicate sync entries.
- Anyone who is not the lead: `/end-session`, always.

## Hard rules

- Never run `/sync-progress` first. The diary entry has to exist before sync reads it.
- Never re-run `/end-session` after `/sync-progress` succeeded. Re-run `/sync-progress`.
- Never run this on anyone else's behalf.
- Never degrade silently to a partial run.
- Never compose client- or reviewer-facing messages from this skill.
- If the consolidation looks wrong, edit `progress_log_path` directly. Never delete a diary
  entry.
