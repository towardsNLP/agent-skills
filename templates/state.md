# Project state

Two files share this shape, and they have **different owners**. That ownership is the whole
concurrency design: one writer per file, so parallel sessions never contend.

| File | Written by | Read by |
|---|---|---|
| `planning/agent/state/<name>.md` | that contributor's `/end-session` | that contributor's `/start-session` |
| `planning/STATE.md` | the lead's `/sync-progress`, and nothing else | anyone wanting an overview |

A contributor's state file is theirs the way their diary is theirs. Never write someone
else's, and never have `/end-session` write the shared one. A single shared file that every
`/end-session` rewrites is a race, and no instruction prevents it.

The shared `planning/STATE.md` is an **index, not a store**: one line per thread pointing at
where the detail lives. Because it is derived, a merge conflict is resolved by regenerating
it, never by hand-merging.

It has a hard budget: **400 words**. Past that it stops being a summary and becomes another
document to read. Anything that does not fit is a pointer, not prose.

Copy the shape below.

---

```markdown
# State

**state_as_of:** YYYY-MM-DD

## Now

- **Branch:** `<current topic branch>`
- **Phase / workstream:** `<id — short name>`
- **Governing spec:** `<path, or "none — gap">`
- **Next action:** `<one concrete sentence>`

## Recent

<!-- newest first, one line each, at most three. Link, never quote. -->

- YYYY-MM-DD — `<title>` → `<progress-log anchor>`
- YYYY-MM-DD — `<title>` → `<progress-log anchor>`
- YYYY-MM-DD — `<title>` → `<progress-log anchor>`

## Open

<!-- at most five. A blocker with no owner and no date is not a blocker, it is a worry. -->

- `<blocker>` — owner, waiting since YYYY-MM-DD
- `<open question>` → `<where it is tracked>`

## In flight

<!-- one line per thread, each tagged: [merged #N] [open PR #N] [in flight <branch>]
     [verified, uncommitted] [reverted #N] [planned, not started] -->

- `[open PR #N]` `<thread>`
- `[in flight <branch>]` `<thread>`

## Watch

<!-- omit entirely when empty -->

- `<at-risk date or dependency named in the profile>`
```

---

## Rules for whoever regenerates it

- **Write only the file you own.** See the table above.

- **Rewrite it whole.** It is a snapshot, not a log. Never append.
- **Set `state_as_of`** to the date of the newest entry it reflects, not today's date. This
  is what lets `/start-session` detect staleness with one `grep` rather than a read.
- **Link, never quote.** A line that quotes the progress log will drift from it.
- **Three recent entries, five open items.** Cut oldest first.
- **No narrative.** If a sentence explains rather than states, it belongs in the diary.
- The word budget is the point. A `STATE.md` that has grown to 1,500 words has recreated the
  problem it was written to solve.
