# Agent skills

Twenty-three skills for Claude Code and other agent hosts, built around one workflow:
**spec-driven development (SDD)**. You and the agent settle a plan, the agent records the
decisions and writes a spec, cuts it into tickets that each carry the check proving them done, and
builds one ticket per fresh session. Later you can review what was built against what you meant.
The rest of the set (sessions, thinking and craft skills) supports that work, and most of it is
useful on its own.

- [Why: the check before the work](#why-the-check-before-the-work)
- [The workflow on one screen](#the-workflow-on-one-screen)
- [A first run](#a-first-run)
- [Install](#install)
- [The skills, by stage](#the-skills-by-stage)
- [Files, writers and derived status](#files-writers-and-derived-status)
- [When not to use it, and what it costs](#when-not-to-use-it-and-what-it-costs)
- [Where it comes from](#where-it-comes-from)
- [Contributing](#contributing)

## Why: the check before the work

One move sits under every skill here: **commit to the check before doing the work.** Each level of
the work has its own check, and the check, written first, is what later proves the work done.

![Five rows, one per altitude: vocabulary, project, feature, unit and experiment, each with the check committed first and the skill that commits it.](docs/figures/check-first.svg)

*A term's definition comes before the components that use it, a component's boundary before its
spec, the spec's acceptance criteria before the tickets, a failing test before the code, and a
predicate and baseline before an experiment runs.*

Three things follow, and they explain most of what the skills refuse to do:

- **Done is derived, never written.** The check was committed up front, so a ticket is done when
  its check passes, not when someone ticks a box.
- **The spec does not pre-write the build.** It holds the intent, the decisions and the acceptance
  criteria; how to build is discovered while building.
- **Tickets may be recut freely; the spec changes only by a dated amendment.** The spec is the
  commitment.

The second idea is about who knows what. The agent sees the code, the documents and what it can
search; you see the product, the people, the history and what you meant. A plan is good when it
comes from where the two overlap, which the philosopher Hans-Georg Gadamer called a *fusion of
horizons*. `/fusion` draws that overlap as a page you think with, before a spec and after it.

![Two overlapping ellipses: the agent's horizon and the user's, with the page in the overlap.](thinking/fusion/figures/two-horizons.svg)

The design behind the workflow is in [`docs/sdd-workflow.md`](docs/sdd-workflow.md), and the page
in [`thinking/fusion/README.md`](thinking/fusion/README.md).

## The workflow on one screen

![The workflow by size of work. A project: a fusion project page, then deconstruct writes the spec map, and each row of the map enters the component lane. One component: grill-me or a fusion page, then adr-spec, tickets, and implement one ticket per fresh session, then your host's code review. Below implement, a fusion review reads the spec and what was built, and sends three arrows back up: re-plan to the planning step, amend to adr-spec, recut or add to tickets. A small change: no spec, tdd, then code review. Coral diamonds mark where you approve; the session skills bracket every working session.](docs/figures/sdd-workflow.svg)

Start from the size of the work:

| The work is | Start with | Then |
|---|---|---|
| **a project**, several specs | `/sdd:fusion` for a project page | `/sdd:deconstruct` writes the spec map; each row then follows the next line |
| **one component**, one spec, with its row in the spec map | `/sdd:grill-me` (questions) or `/sdd:fusion` (a page) | `/sdd:adr-spec`, then `/sdd:tickets`, then `/sdd:implement` once per ticket |
| **a small change** that does not alter a spec's scope | no spec | `/sdd:tdd`: a failing test, the code, a clean-up |

In Claude Code the plugin's skills take the `/sdd:` prefix, so the figure's `/fusion` is typed
`/sdd:fusion`.

Every spec takes its kind (build, experiment or knowledge revision) and its parent from a row in the
spec map, and `/sdd:adr-spec` stops without one. A project with no spec map yet starts at the first
line; for a product's very first component, `/sdd:fusion` plans it and `/sdd:deconstruct` registers
its row.

<details><summary>Words used here</summary>

- **Spec map**: the project's planned list of specs, one row each, with its kind and the row it
  belongs under (its parent). `/sdd:deconstruct` writes it.
- **Kinds of work**: *build* changes what the system does; *experiment* changes what the project
  can claim from a measurement; *knowledge revision* changes a governed model, rule or source.
- **Seams**: the places where a spec's work will be verified, named before any check exists.
- **ADR**: an architecture decision record, one decision and why.
- **Lead**: the person who consolidates the team's progress into the shared planning documents.
- **Proof loop**: how `/sdd:implement` proves a ticket for its kind of work: red, green, refactor
  for build; register, run, evaluate for an experiment; query, revise, validate provenance for a
  knowledge revision.

</details>

**Where you approve.** The agent proposes and you decide, at five points: each fork on a fusion
page; the spec map; each architecture decision record (ADR), one at a time; the spec, after you
read its scope (§3) and its seams and acceptance (§5); and the list of tickets.

**Sessions.** A grilling, `/sdd:adr-spec` and `/sdd:tickets` run in one session, because the
interview is the thinking the spec rests on. A finished fusion page is the exception: it holds
that thinking in a file, so a fresh session can resume it. Each `/sdd:implement` gets a fresh
session of its own. `/sdd:start-session` and `/sdd:end-session` open and close every working
session, and a lead also runs `/sdd:sync-progress`.

**Review.** `/sdd:fusion` can also revisit a spec at any stage after `/sdd:adr-spec`, comparing what
was meant, what the spec committed to and what was built. The spec's owner rules on each finding:
an amendment, new tickets, or a new plan. The code review before a merge is your host's own; no
skill here replaces it.

## A first run

One developer adds CSV export to the monthly report of an invented app, whose spec map already has
a row for it, `R.2`. Read it before installing; the commands work once [Install](#install) is done. Each step says what it produces and what to run
next. Open a step to see what it writes.

**0. Open the session.** `/sdd:start-session` prints a short card: where the work stands and what
is ready. Each session below ends with `/sdd:end-session`.

**1. Settle the plan.** In Claude Code:

```
/sdd:grill-me add CSV export of the monthly report
```

The agent asks the decisions that are still open, a round at a time, each with its recommended
answer, and stops when none is left. For a bigger or less familiar change, `/sdd:fusion` draws the
plan as a page instead, with its frame, its forks and what the agent cannot see. *Next, in the same
session:* `/sdd:adr-spec`.

<details><summary>What a round looks like</summary>

```
1. Which columns does the export carry: the report's visible columns, or every field?
   Recommended: the visible columns, so the file matches what the user sees.
2. Who may export: anyone who can view the report, or only its owner?
   Recommended: anyone who can view it; the data is already on their screen.
```

</details>

**2. Record the decisions, then the spec.**

```
/sdd:adr-spec
```

Run in the same session, it takes the subject from the interview and the component's row from the
spec map, and asks you to confirm the spec's ID and name before writing. It proposes each decision
that clears your project's bar for an ADR (the README in your decision-records directory), one at a
time, and you rule on each in chat. Then it writes `spec.md`. Read its scope (§3) and its seams and acceptance (§5)
before you approve; once approved, the spec is frozen, and later changes become dated amendments.
*Next, in the same session:* `/sdd:tickets`.

<details><summary>What the spec's §3 and §5 look like</summary>

```markdown
## 3. Scope
- **IN**: a "Download CSV" action on the monthly report; its visible columns; UTF-8 with a header row.
- **OUT**: other reports; formats other than CSV.
- **DEFERRED**: scheduled exports, to a later spec, once someone asks for them.

## 5. Seams and acceptance
### Seams
The report's query layer, which already returns the visible columns.

### Automated checks
**V1** — visible columns only — `pytest tests/reports/test_export.py::test_visible_columns_only` —
a report with 3 visible columns exports a header row and 3 columns.
**V2** — access respected — `pytest tests/reports/test_export.py::test_export_respects_access` —
a user who cannot view the report gets no export.
```

</details>

**3. Cut the tickets.**

```
/sdd:tickets
```

The agent cuts the spec into tickets, each one unit of work sized to one fresh session and proved
by a named check, with the tickets that must land first. You approve the list, and it reports which
tickets can start now. *Next:* end this session, and open a fresh one per ticket.

<details><summary>What a ticket looks like</summary>

```markdown
# 01 — the monthly report exports its visible columns as CSV

**What becomes true:** a viewer of the monthly report can download it as a CSV with a header row
and the report's visible columns.

**Blocked by:** none (can start immediately)
**Governs:** spec R.2 §3 and §5; ADR 0007
**check_type:** test
**check:** `tests/reports/test_export.py::test_visible_columns_only`
**Claimed by:** unclaimed

## Outcome
```

</details>

**4. Build one ticket per fresh session.**

```
/sdd:implement planning/tickets/R.2/01-csv-export.md
```

The agent claims the ticket, loads only what it names, works test-first, and closes it by running
its check and writing its Outcome: the change identifier (a PR number, for example) and anything
that diverged from the plan. When every ticket of the spec has an Outcome, it writes the spec's
acceptance record, grading each requirement. *Next:* your host's code review, then merge.

<details><summary>What an Outcome looks like</summary>

```markdown
## Outcome

**PR:** #42
**Diverged:** the header row uses the column labels, not the field names; the spec says "header
row" and does not choose.
```

</details>

**5. See what is done.** Your project's status command runs each ticket's check and prints the
board, as under [derived status](#derived-status), with the next tickets ready to take. Nobody writes
"done" by hand.

**Later: review it.** `/sdd:fusion review spec R.2` compares what you meant, what the spec says and
what was built. The spec's owner (named in the spec) rules on each finding; an amendment then goes
through `/sdd:adr-spec`, and new tickets through `/sdd:tickets`.

## Install

**In Claude Code, the whole set** installs as a plugin, per project. Add this to the project's
`.claude/settings.json`, merging it if the file exists:

```json
{
  "extraKnownMarketplaces": {
    "towardsnlp-agent-skills": {
      "source": { "source": "github", "repo": "towardsNLP/agent-skills" }
    }
  },
  "enabledPlugins": { "sdd@towardsnlp-agent-skills": true }
}
```

Open Claude Code in the project and trust the folder. **Check:** typing `/sdd:` lists the skills.
If nothing is listed, check that the folder is trusted and the two keys are in place, then run
`/plugin marketplace update towardsnlp-agent-skills`. Once the profile below is in place,
`/sdd:start-session` prints a session card.

**In other hosts,** the thinking, knowledge and craft skills install from a clone of this
repository with `./bin/link.sh`, which links them into `~/.claude/skills` and `~/.agents/skills`.
Start a new session afterwards. Codex calls a skill with `$name` rather than `/name`, so typing
`$grill-me` there should start an interview; Cursor, which reads both folders, may list each skill
twice. The SDD and session skills have no install path outside Claude Code yet.

**Then, in your project:**

1. **The profile.** Copy [`templates/profile.md`](templates/profile.md) to
   `planning/agent/profile.md`. Every skill reads its project-specific paths and values from that
   one file. For the SDD skills, start with `spec_map_path`, `spec_dir`, `spec_path_pattern`,
   `ticket_dir`, `decision_records`, `glossary_path`, `workstream_id_scheme`, `phase_vocabulary`,
   `test_command` and `ticket_status_command`; add `fusion_dir` if you use `/sdd:fusion`.
2. **A spec map and a glossary.** `/sdd:deconstruct` writes the spec map at `spec_map_path`, and it
   needs a glossary at `glossary_path` first: it will not decompose a project whose terms are not
   named.
3. **A README in your decision-records directory** that says what deserves an ADR. `/sdd:adr-spec`
   tests each candidate against that bar.
4. **The status tool.** `make sync-tools TO=<your project root>`, run from a clone of this
   repository, copies `tools/ticket_status.py` into your project. Set `ticket_status_command` to
   what runs it there, for example `python3 tools/ticket_status.py`.

<details><summary>If a skill does not load, or behaves differently for a teammate</summary>

The plugin's skills are namespaced (`/sdd:`), so nothing shadows them. The trap is a copy left
behind: a skill the project still commits in its own `.claude/skills` folder is silently shadowed
by anyone's personal skill of the same name, so two people run different versions with no warning.
After moving to the plugin, delete the project's old committed copies. The two install scopes, why the
personal set is symlinked, and what each skill costs in context are explained in
[`docs/install.md`](docs/install.md).

</details>

## The skills, by stage

*You* means you type it; *the agent* means the agent may also reach it on its own.

| Stage | Skill | Called by | What it is for |
|---|---|---|---|
| **Plan** | `fusion` | you | A page you think with, before a spec or a spec map, or to review a spec already written. Draws where the plan sits, the frame and a rival, the alternatives, what the agent cannot see, and the forks, revised in rounds until you call it finished. [Explainer.](thinking/fusion/README.md) |
| | `grill-me` | you | The interview, typed: rounds of questions, each with a recommended answer. |
| | `grilling` | the agent | The interview primitive behind `grill-me`. Facts are the agent's job; decisions stay yours. |
| | `grill-with-docs` | you | `grilling` and `domain-modeling` together, so the interview leaves a paper trail. |
| | `domain-modeling` | the agent | Challenges a term against the glossary, sharpens fuzzy language, and writes the term down. |
| **Commit** | `deconstruct` | you | Breaks a project into build, experiment and knowledge-revision components with their dependency edges, and writes the spec map. |
| | `adr-spec` | you | Records the decisions, one ADR at a time, then writes a frozen spec or a dated amendment. |
| | `check-contracts` | you | Checks code, data and knowledge names against the project's declared authorities. |
| **Build** | `tickets` | you | Cuts a spec into tickets, each independently verifiable by a named check and sized to one session. |
| | `implement` | you | Builds one ticket through the proof loop its kind of work needs, and records what diverged. |
| | `tdd` | the agent | Red, green, refactor, one vertical slice at a time. |
| | `codebase-design` | the agent | A shared vocabulary for designing modules that hide a lot behind a small interface: interface, depth, seam, adapter. |
| **Sessions** | `start-session` | you | Returns a bounded session card. Read-only. |
| | `end-session` | you | Logs the session to your own diary and regenerates your own state file. |
| | `sync-progress` | you | Consolidates the diaries into the shared planning documents. Lead only. |
| | `wrap-day` | you | `end-session`, then `sync-progress`, stopping if the first fails. |
| **Thinking and craft** | `research` | the agent | Sends reading to a background agent; findings come back as a cited Markdown file. |
| | `writing-for-agents` | the agent | How to write any document an agent reads. Read it before editing a `SKILL.md`. |
| | `to-questionnaire` | you | Turns a decision you cannot make alone into a questionnaire for the person who can. |
| | `teach` | you | Teaches a concept over several sessions. It claims the current folder, so run it in a dedicated one. |
| | `unslop` | you | Cuts AI tells from prose meant for outside readers. |
| | `show-me-your-work` | you | A decision log, one row per decision, for long or unattended runs. On trial. |
| | `handoff` | you | Compacts the conversation into a handoff document for a fresh session. |

## Files, writers and derived status

![Each skill and the one file it writes: fusion its pages, deconstruct the spec map, adr-spec the ADRs, the spec and its amendments, tickets the ticket files, implement each Outcome and the acceptance record, end-session your diary and state, sync-progress the shared state; the status tool writes nothing.](docs/figures/who-writes-what.svg)

**One writer per file.** A ticket is the one file with two writers, one per phase: `/sdd:tickets`
writes it, and only `/sdd:implement` writes its Outcome and claim. That is the whole concurrency
design: no two sessions write the same file, and a ticket's claim stops two people taking the same
work. All paths come from the project profile.

### Derived status

Nothing in the workflow writes down whether work is done. `tools/ticket_status.py` derives it by
running each ticket's own check, and its exit code is the point: it fails when a ticket carries an
Outcome but its check fails, when a check no longer resolves, when a ticket is blocked by one that
does not exist, when a planned component has no spec, or when a spec has no tickets.

```
R.2-csv-export  [1/4 done]
   01 the monthly report exports its visible colu done    test    dana
   02 a viewer without access gets no export      open    test    dana
   03 the header row uses the column labels       FAIL    test    -
   04 support confirms the file opens in a sprea  manual  manual  -

drift (1):
  R.2-csv-export/03: closed, but its check fails
```

The second column is each ticket's `check_type`: *test* runs a test, *manual* needs a person to
confirm and record it.

`open` and `FAIL` are different claims. Open means not built yet, which is most of a live board.
FAIL means the Outcome asserts work the check does not support: the one this exists to catch.

A spec and its tickets pair under either name form: `planning/tickets/R.2/` and
`planning/tickets/R.2-csv-export/` both belong to the spec directory carrying that slug. The
spec map's ID column is what makes them equivalent.

The tool uses the standard library only, so vendoring it is one file copy, and a project's CI can
diff its copy against this source.

It derives rather than reads for a measured reason: across three repositories, **95 acceptance
boxes were written into specs and not one was ever ticked** (see
[`docs/sdd-workflow.md`](docs/sdd-workflow.md), *The evidence*). A status a human must remember to
update is a status that lies.

## When not to use it, and what it costs

- **A small change needs no spec.** A bug fix or a change inside one spec's scope is worked
  test-first. A divergence found while building a ticket goes in that ticket's Outcome, not in a
  new spec.
- **A spec costs review time.** Specs here are kept to intent, decisions and acceptance; design
  detail goes to a contract, an ADR or nowhere, so there is less to read. You still read §3 and §5
  before approving.
- **Interviews end.** A grilling stops when no decision is left, and a fusion page asks only what
  needs you; a decision that needs nothing only you hold becomes a default you can veto.
- **Sessions cost context.** Planning, the spec and the tickets share one session; each ticket gets
  a fresh one. Every skill's description loads in every session of a project using the plugin, and
  [`docs/install.md`](docs/install.md) shows how to trim that.
- **No speed claims.** We have not measured whether this makes anyone faster.

## Where it comes from

![Anthropic's interview-then-spec loop, made into skills by mattpocock/skills; pstack's skills and principles; what this repository adapted from each, and what it wrote: deconstruct, check-contracts, the session skills and fusion.](docs/figures/lineage.svg)

The loop at the centre is public. Anthropic's Thariq Shihipar described it in December 2025, and the
[Claude Code best practices](https://code.claude.com/docs/en/best-practices) now suggest asking the agent to interview
you until it could write the spec, then building it in a fresh session. Matt Pocock turned it into
skills in [mattpocock/skills](https://github.com/mattpocock/skills), and Lauren Tan's
[pstack](https://github.com/cursor/plugins/tree/main/pstack) contributed two skills and two
principles. What this repository adds is a commitment that runs through every level: decisions
recorded before the spec, a frozen spec with dated amendments, tickets proved by checks with
derived status, a project-level decomposition, the session skills, and `/fusion`. Its nearest
relative in the field is [Plannotator](https://github.com/backnotprop/plannotator), which opens an
agent's plan in a browser page to annotate. The explainer's [*Where this comes
from*](thinking/fusion/README.md#where-this-comes-from) and [*The field it belongs
to*](thinking/fusion/README.md#the-field-it-belongs-to) place it among spec-driven development
tools.

### Origins and pinned provenance

[`UPSTREAM.toml`](UPSTREAM.toml) pins the source repository, full commit SHA, upstream path,
licence, comparison date, local status and change summary for every borrowed skill. A test
([`tests/test_upstream_manifest.py`](tests/test_upstream_manifest.py)) protects the content hash of
each `vendored` `SKILL.md`; a local edit must reclassify it as `adapted`.

| Source | Skills |
|---|---|
| Written here | `start-session` `end-session` `sync-progress` `wrap-day` `check-contracts` `deconstruct` `fusion` |
| [mattpocock/skills](https://github.com/mattpocock/skills) (MIT), vendored | `research` `to-questionnaire` `codebase-design` `teach` |
| mattpocock/skills, adapted | `writing-for-agents` `grilling` `grill-me` `grill-with-docs` `handoff` `tdd` `domain-modeling` |
| [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack), adapted | `unslop` `show-me-your-work`; `start-session` also uses two pstack principles as inspiration |
| Merged, then diverged | `adr-spec`: an earlier local `new-spec` plus Pocock's `to-spec`. The local one created a shell and refused to fill the hard sections; his synthesises the whole document from the conversation. The difference is whether thinking happened first, so the refusal became a *precondition* rather than a property. Then it diverged: decisions are recorded before the spec rather than assumed to exist, design detail is triaged to a contract or an ADR or nowhere, there is no task table, and no user stories. |
| Adapted | `tickets`, from Pocock's `to-tickets`. Kept: tracer bullets, blocking edges and working the frontier, one-context-window sizing, prefactoring first, expand–contract for wide refactors, never modifying the parent. Changed: tickets are durable rather than throwaway, independently *verifiable* rather than vertically sliced, and doneness is derived from a named check rather than ticked in a box. |
| Reimplemented under the same generic name | `implement`. Pocock's is five lines and never touches the ticket, which is coherent when tickets are throwaway on a tracker. This one claims, loads only what the ticket names, selects a proof loop by work kind, and closes by recording what diverged. |

The session set began as one copy per repo and drifted: 24 files, roughly 3,300 lines, five
archetypes duplicated across five repositories, each fork accumulating its own edits. A lesson
learned in one place reached the others only when someone hand-carried it. Deduplicated in
September 2026.

`start-session`'s isolated-worker path and the one-writer-per-file rule come from pstack's
`principle-guard-the-context-window` and `principle-separate-before-serializing-shared-state`:
route discovery outside the main context and return only a bounded card; eliminate a shared write
target rather than trying to lock it.

Every skill has an `agents/openai.yaml` sidecar for OpenAI UI metadata and invocation policy. The
sidecar is a host adapter, not a second copy of the workflow. Its policy must match
`disable-model-invocation` in `SKILL.md`; a contract test checks the pair.

**Moved out:** `okf-creator` now lives in its own repository. **Not adopted:** Pocock's `wayfinder`
and `code-review`; `code-review` would also shadow Claude Code's built-in command of that name.

## Contributing

**The skills carry the workflow; the project carries its own facts.** No skill here names a
project, a client, a person or a company. Everything that differs between repos (the contributor
roster, document paths and their precedence, the spec ID scheme, phase vocabulary, branch rules,
gates, read-only paths, forbidden terms, deadlines, stakeholders) lives in one file per repo at
`planning/agent/profile.md`. If a skill needs a project's value, add a key to the profile rather
than branching inside the skill: a skill that names one project stops being shareable.

**Adding a skill.** Put it in the directory that matches what it is for, and, if it is
personal-scope, run `./bin/link.sh`. Every skill must also be listed in
`.claude-plugin/plugin.json`; `tests/test_plugin_manifest.py` fails on one this repo holds but the
manifest omits. Read `writing-for-agents` first, and default to `disable-model-invocation: true`
unless the agent genuinely has to reach the skill on its own. `make test` runs the suite and
`make lint` the linter.

## Licence

MIT, see [`LICENSE`](LICENSE). Vendored skills remain under their own terms; the provenance table
above records each one.
