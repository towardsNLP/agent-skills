# Agent skills

Nineteen skills for Claude Code and Codex, grouped by what they are for. Some I wrote, some I
adapted, some are vendored unchanged with attribution.

```
session/     start-session  end-session  sync-progress  wrap-day
sdd/         check-contracts  to-spec
thinking/    grilling  grill-me  grill-with-docs  research
             writing-for-agents  to-questionnaire  teach
knowledge/   domain-modeling
craft/       tdd  unslop  show-me-your-work  codebase-design  handoff
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
reaching them on its own. **User-invoked** skills (`disable-model-invocation: true`) cost nothing
and are invisible to the model — which makes me the index that has to remember they exist. That
trade is deliberate: **6 of 19 are model-invoked.**

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
| `to-spec` | user | Create a spec, and fill it from the grilling that earned it. |
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
| `planning/specs/` and the roadmap row | `to-spec` |

## Origins

| Source | Skills |
|---|---|
| Mine, written from scratch | `start-session` `end-session` `sync-progress` `wrap-day` `check-contracts` |
| [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), unmodified | `writing-for-agents` `grilling` `grill-me` `grill-with-docs` `research` `handoff` `to-questionnaire` `codebase-design` `tdd` `teach` |
| mattpocock/skills, adapted | `domain-modeling` — resolves its glossary and decision-record targets from `planning/agent/profile.md` instead of assuming `CONTEXT.md`, and never creates a second glossary |
| [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack), unmodified | `unslop` |
| pstack, adapted | `show-me-your-work` — two Cursor-specific references repointed: the transcript path, and the cross-model reviewer, which now says "prefer a different model family where the harness offers one" rather than assuming one exists |
| Merged | `to-spec` — my `new-spec` plus Pocock's `to-spec`. Mine created a shell and refused to fill the hard sections; his synthesises the whole document from the conversation. Both are right about different situations, and the difference is whether thinking happened first — so the refusal became a *precondition* rather than a property. His issue-tracker publishing and user-stories section are dropped. |

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
start-session  →  [grill-me → to-spec → tickets]  →  work  →  end-session
                                                              lead also: sync-progress
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
