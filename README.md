# Agent skills

Twenty-two skills for Claude Code and Codex, grouped by what they are for. Some I wrote, some I
adapted, some are vendored unchanged with attribution.

```
session/     start-session  end-session  sync-progress  wrap-day
sdd/         deconstruct  adr-spec  tickets  implement  check-contracts
thinking/    grilling  grill-me  grill-with-docs  research
             writing-for-agents  to-questionnaire  teach
knowledge/   domain-modeling
craft/       tdd  unslop  show-me-your-work  codebase-design  handoff

tools/       ticket_status.py     derives doneness; the workflow writes none
templates/   profile.md  state.md
```

## Two install scopes, and the trap between them

The grouping is not cosmetic: **`session/` and `sdd/` are project-scope, the other three are
personal-scope**, and the two install completely differently.

| Scope | Directories | How it installs | Who gets it |
|---|---|---|---|
| **Project** | `session/` `sdd/` | as a plugin, declared in a repo's `.claude/settings.json` | everyone who clones that repo |
| **Personal** | `thinking/` `knowledge/` `craft/` | `bin/link.sh` symlinks them into `~/.claude/skills` and `~/.agents/skills` | me, in every project |

Claude Code resolves same-named skills in this order:

    enterprise > personal (~/.claude/skills/) > project (.claude/skills/) > bundled

A personal skill **silently shadows** a project skill of the same name — no warning, no error.
Hold a personal copy of `start-session` while a repo commits its own and you run your version
while your collaborators run theirs. This is why `bin/link.sh` links only the three
personal-scope directories, and why the project set ships namespaced as `/sdd:start-session`.

## Installing

**Personal set:** `./bin/link.sh`. Editing a skill here updates every install at once. Re-run
after adding, removing or renaming one.

**Project set:** see [`docs/install.md`](docs/install.md). Two keys in the repo's
`.claude/settings.json`, plus a `planning/agent/profile.md` copied from `templates/`.

### Why symlinks into `~` rather than a shared folder

Claude Code walks *up* the directory tree looking for `.claude/skills`, but **stops at the git
repo root**. Measured with a probe skill, not assumed: placed in a parent folder, it was ABSENT
from a session started inside a nested git repo and FOUND from a sibling folder that was not a
repo. Every real project is a repo, so a `.claude/skills` in a parent folder is invisible from
inside all of them. User scope is the only location that works everywhere.

## The one rule that makes the project set shareable

**The skills carry the workflow. The project carries its own facts.**

No skill here names a project, a client, a person or a company. Everything that differs between
repos — the contributor roster, document paths and their precedence, the spec ID scheme, phase
vocabulary, branch rules, gates, read-only paths, forbidden terms, deadlines, stakeholders —
lives in one file per repo at `planning/agent/profile.md`. Copy `templates/profile.md` to start
one.

If a skill needs a project's value, **add a key to the profile rather than branching inside the
skill.** A skill that names one project stops being shareable.

## Invocation cost

**Model-invoked** skills cost a permanent description slot in context, in exchange for the agent
reaching them on its own. **User-invoked** skills (`disable-model-invocation: true`) are invisible
to the model — which makes me the index that has to remember they exist. **6 of 22 are
model-invoked.**

**A user-invoked skill is not free.** Measured 2026-09-23 in a session with 32 skills loaded: the
nine project skills, every one of them `user-only`, cost **~560 tokens**, and seven personal
user-only skills another **~280**. `disable-model-invocation` changes *who can reach* a skill, not
whether its description is loaded. The README said otherwise until this was measured; the lesson
is the one `docs/install.md` already stated — measure with `/context` rather than reasoning from
what a flag sounds like it does.

The lever that actually reduces the cost is `skillOverrides`: `"name-only"` keeps a skill
invokable while suppressing its description, `"off"` hides it entirely.

`skillOverrides` in settings trims the rest: `"name-only"` keeps a skill invokable but suppresses
its description; `"off"` hides it.

## What each one is for

| Skill | Invocation | What it is for |
|---|---|---|
| `start-session` | user | Load the minimum context the task needs and produce a task brief. Read-only. |
| `end-session` | user | Log the session to your own diary and regenerate your own state file. |
| `sync-progress` | user | Consolidate diaries into the shared planning documents. Lead only. |
| `wrap-day` | user | Run `end-session` then `sync-progress`, aborting if the first fails. |
| `check-contracts` | user | Validate a name, path, ID or output against the project's conventions. |
| `deconstruct` | user | Break a whole project into the set of specs it needs, with dependency edges. Project level, run rarely. |
| `adr-spec` | user | Record the decisions, then write the spec against them. The spec is frozen at approval. |
| `tickets` | user | Cut an approved spec into tracking records, each independently verifiable by a named check. |
| `implement` | user | Build one ticket in a fresh session: claim, work at the spec's seam, run the check, record the outcome. |
| `grilling` | model | The interview primitive. Works a design tree in rounds, asks the whole frontier at once with a recommendation per question, and waits. Facts are the agent's job; decisions stay mine. |
| `grill-me` | user | Typed entry point to `grilling`. |
| `grill-with-docs` | user | `grilling` + `domain-modeling` together, so the interview leaves a paper trail. |
| `research` | model | Delegates reading to a background agent: primary sources only, findings written to a cited Markdown file. |
| `writing-for-agents` | model | How to write any document an agent reads: context pointers, the two loads, the information hierarchy, completion criteria, no-ops. Read it before editing a SKILL.md or an AGENTS.md. |
| `to-questionnaire` | user | Turns a decision I cannot make alone into a questionnaire for the person who can. Interviews me about the *send*, then aims the questions at the gap. |
| `teach` | user | Teach a concept over multiple sessions. **Claims the current directory** as a stateful workspace, so run it in a dedicated folder, never inside a project repo. |
| `domain-modeling` | model | Challenge a term against the glossary, sharpen fuzzy language, stress-test with invented scenarios, check the code agrees, write it down inline. |
| `tdd` | model | Red-green-refactor, one vertical slice at a time. Its own guardrails tell it to skip when the test path is unclear or integration-heavy, so it stays quiet on experiment work. |
| `unslop` | user | Cuts AI tells from prose. 33 numbered rules. For anything an outside reader sees. |
| `show-me-your-work` | user | A TSV decision log, one row per decision, evidence as a pointer. For long or unattended runs. On trial. |
| `codebase-design` | model | Deep-module vocabulary: module, interface, depth, seam, adapter, leverage, locality. Maps onto a ports-and-adapters layout directly. |
| `handoff` | user | Compacts the conversation into a handoff document for a fresh session. |

## Who writes what

One writer per file. This is the whole concurrency design, and it is why parallel sessions never
contend:

| File | Only writer |
|---|---|
| `planning/diaries/<name>-diary.md` | that contributor's `end-session` |
| `planning/agent/state/<name>.md` | that contributor's `end-session` |
| `planning/STATE.md` | the lead's `sync-progress` |
| progress log, roadmap, plan | the lead's `sync-progress` |
| `planning/spec-map.md` | `deconstruct` |
| `planning/specs/<id>/spec.md` | `adr-spec`, once, then never again |
| `planning/specs/<id>/acceptance.md` | `implement`, at spec close |
| `planning/tickets/<id>/NN-*.md` | `tickets` writes them, `implement` closes them |

## Derived status

Nothing in this workflow writes down whether work is done. `tools/ticket_status.py` derives it by
running each ticket's own check, and the exit code is the point — it is non-zero when a ticket
carries an Outcome but its check fails, when a check no longer resolves, when a ticket is blocked
by one that does not exist, when a planned component has no spec, or when a spec has no tickets.

```
P1-rule-engine  [2/5 done]
   01 the YAML loader rejects an ungoverned predic done    gate    ahmad
   03 the evaluator fires rules in priority order  open    gate    ahmad
   04 the contradiction post-pass defeats the weak FAIL    gate    -
   05 the SME confirms the tier assignment for fam manual  manual  -

drift (1):
  P1-rule-engine/04: closed, but its check fails
```

`open` and `FAIL` are different claims. Open means not built yet, which is most of a live board.
FAIL means the Outcome asserts work the check does not support — the one this exists to catch.

Standard library only, so vendoring is a single file copy: `make sync-tools TO=<project root>`,
and the project's CI diffs its copy against this source. `make test` runs the suite.

The reason it derives rather than reads: across three repositories, **95 acceptance boxes were
written into specs and not one was ever ticked.** A status a human must remember to update is a
status that lies.

## Origins

| Source | Skills |
|---|---|
| Mine, written from scratch | `start-session` `end-session` `sync-progress` `wrap-day` `check-contracts` `deconstruct` |
| [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), unmodified | `writing-for-agents` `grilling` `grill-me` `grill-with-docs` `research` `handoff` `to-questionnaire` `codebase-design` `tdd` `teach` |
| mattpocock/skills, adapted | `domain-modeling` — resolves its glossary and decision-record targets from `planning/agent/profile.md` instead of assuming `CONTEXT.md`, and never creates a second glossary |
| [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack), unmodified | `unslop` |
| pstack, adapted | `show-me-your-work` — two Cursor-specific references repointed: the transcript path, and the cross-model reviewer, which now says "prefer a different model family where the harness offers one" rather than assuming one exists |
| Merged, then diverged | `adr-spec` — my `new-spec` plus Pocock's `to-spec`. Mine created a shell and refused to fill the hard sections; his synthesises the whole document from the conversation. The difference is whether thinking happened first, so the refusal became a *precondition* rather than a property. Then it diverged: decisions are recorded before the spec rather than assumed to exist, design detail is triaged to a contract or an ADR or nowhere, there is no task table, and no user stories. |
| Adapted | `tickets` — from Pocock's `to-tickets`. Kept: tracer bullets, blocking edges and working the frontier, one-context-window sizing, prefactoring first, expand–contract for wide refactors, never modifying the parent. Changed: tickets are durable rather than throwaway, independently *verifiable* rather than vertically sliced, and doneness is derived from a named check rather than ticked in a box. |
| Same name, different skill | `implement` — Pocock's is five lines and never touches the ticket, which is coherent when tickets are throwaway on a tracker. This one claims, loads only what the ticket names, works at the seam the spec already chose, and closes by recording what diverged. |

The session set began as one copy per repo and drifted: 24 files, roughly 3,300 lines, five
archetypes duplicated across five repositories, each fork accumulating its own edits. A lesson
learned in one place reached the others only when someone hand-carried it. Deduplicated in
September 2026.

`start-session`'s subagent fallback and the one-writer-per-file rule come from pstack's
`principle-guard-the-context-window` and `principle-separate-before-serializing-shared-state`:
route bulk reading to subagents and keep summaries in the main thread; eliminate a shared write
target rather than trying to lock it.

Codex `agents/openai.yaml` sidecars were dropped throughout — they configure a Cursor-side policy
that does not apply here.

**Moved out:** `okf-creator` now lives in its own repository. It is text an agent reads *plus a
library a program imports*, which is a different artefact with a different consumer and release
cadence. It is still symlinked into `~/.claude/skills` from there.

**Not adopted:** Pocock's `wayfinder` and `code-review`. `code-review` additionally shadows Claude
Code's built-in command of that name, since personal skills outrank bundled ones.

## The workflow

```
deconstruct  →  grill-me  →  adr-spec  →  tickets  →  implement  →  review → ship
  project        ──── one session ────      one fresh session per ticket

start-session  →  <the above>  →  end-session        lead also: sync-progress
```

Keep grilling and the documents it produces in **one unbroken context window**. The interview is
the thinking; splitting it away from the writing throws that thinking out.

The design behind the spec and ticket skills is in
[`docs/sdd-workflow.md`](docs/sdd-workflow.md).

## Adding a skill

Drop it in the directory that matches what it is for, and — if it is personal-scope — run
`./bin/link.sh`. Project-scope skills must also be listed in `.claude-plugin/plugin.json`.

Read `writing-for-agents` first. Default to `disable-model-invocation: true` unless the agent
genuinely has to reach the skill on its own.

## Licence

MIT, see [`LICENSE`](LICENSE). Vendored skills remain under their own terms; the Origins table
above records each one.
