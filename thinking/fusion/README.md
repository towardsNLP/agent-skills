# Fusion: co-thinking with an agent through a page

`/fusion` is a way for a person and an AI agent to plan together, and to review what they planned.
Instead of interviewing you one question at a time, the agent draws the plan as a page you think
with: where it sits, the frame it is argued in, the alternatives, what the agent cannot see, and
the decisions that need you. You answer on the page. The page changes, round by round, until you
call it finished. Then the next skill takes it on: a spec map, a spec, an amendment, or tickets.

This document explains the idea, the page and the practice. The skill itself is
[`SKILL.md`](SKILL.md); what each section of a page holds is in
[`references/anatomy.md`](references/anatomy.md).

A few words used throughout. A **skill** is a set of instructions an agent loads for one kind of
task; `/fusion` is one. A **spec** is the written specification of one component, which the build
follows; a **spec map** lists a project's planned specs; an **amendment** is a dated, approved change
appended to a spec once it is frozen; a **ticket** is one unit of work with the check that proves it
done. An **ADR** (architecture decision record) records one decision and why. A **grilling** is an
interview skill that settles decisions one round of questions at a time. A **round** is one exchange: you answer, and the page
changes. The **frame** is how the problem is cut: by user need, by structure, by source, or
another way. Items on a page carry IDs: **F** a fork (a decision that needs you), **D** a default
(yours to veto), **A** an assumption, **E** a question only you can answer, **R** a ruling already
made. The teach-back, the resumption check and drift are explained where they come up.

## Two horizons, one page

![Two overlapping ellipses: the agent's horizon on the left, the user's on the right, and the page in the overlap.](figures/two-horizons.svg)

*Figure 1. Two horizons and the page drawn where they overlap. What only the agent can retrieve
reaches the page as grounding (the commit or dated documents its facts were checked against),
anchors (files, commits and links a reader can open) and precedents. What only you hold reaches it as "where my
view ends" and as the decisions you rule.*

Hans-Georg Gadamer described understanding as a *fusion of horizons* (*Truth and Method*, 1960).
A horizon is the range of what someone can see and understand from where they stand. It is formed
by their history, their language and what they already know, and it moves as they learn.
Understanding someone is neither giving up your own view nor copying theirs. The two horizons
overlap, and each grows.

Planning with an agent has the same shape. The agent sees from the code, the documents and
whatever it can search. You see from the product, the people, the history and what you meant. Each
of you is blind to much of what the other sees. The plan should come out of the overlap, and the
overlap needs a place to happen. A fusion page is built to be that place.

The situation a plan sits in (the system, the roadmap, the components around it) is its
**context**. The context is part of what both of you look at; a horizon is where each of you looks
from. The distinction matters in review, below.

## Why a page, and not a list of questions

A common way to settle a plan with an agent is a grilling: the agent asks numbered questions,
each with a recommended answer, and you rule on them. Grilling is quick, but a decision can only be
judged against the model it belongs to. A list of questions hands you the decisions, while the
model they belong to stays with the agent. You can choose inside its frame, but nothing in the list is set aside for
saying the frame is wrong, and that may be the most valuable thing you know.

A page hands you the model first. Each part of its design answers a way that question lists fail:

- **The frame is on the page, with a rival.** The agent states the cut it chose, why, and at least
  one other way to cut the problem, with what the plan would become under it. You can take the
  rival, or bring a third.
- **What is at stake comes before the options.** Every decision that needs you is a *fork*, and each fork card
  says, in a concrete case, the moment the options lead to different outcomes, what that changes
  downstream, and what it would cost to reverse. Consequences are what make a decision worth your
  attention. Options alone are not.
- **The agent says where its view ends.** A section lists the facts only you hold (history,
  people, commitments, intent) as questions you may skip. A fork whose "needs you" field would be
  empty is not a fork at all: it becomes a **default**, listed for you to veto.
- **Context is drawn once, in figures.** The page draws the whole the decision belongs to, in a
  shared colour key, so you see the structure before you read about it.
- **Every change is marked.** Round after round, the page opens with what moved since you last
  read, so a re-read starts from what changed.

Recent studies of people planning with agents point the same way, though none tests a page like
this one. In a study of a spreadsheet agent's plan mode, participants answered 88 of 99 clarifying
questions but only 2 of 24 edited the plan itself, and 44% of the requirements came from those
answers ([Kumar et al., 2026](https://arxiv.org/abs/2607.23670)): in that study, people
contributed through questions rather than by editing the plan. Involving users in planning helped
flawed plans and made sound ones worse ([He et al., CHI 2025](https://arxiv.org/abs/2502.01390)),
which fits turning a decision that needs nothing only you hold into a default rather than a
question. In a small pilot, people
accepted wrong plans half as often when the plan was drawn as a graph
([AIPOM, 2025](https://arxiv.org/abs/2509.24826)). And the two shipping plan modes linked here show
the plan as prose with one approval gate, with no forks, rival frame or questions for the human ([Cursor](https://cursor.com/blog/plan-mode);
[Claude Code](https://code.claude.com/docs/en/permission-modes)).

The page does not replace grilling. Small, local forks can still go to a quick grilling round,
asked against the page.

## Where this comes from

The pipeline `/fusion` belongs to (interview, spec, tickets, one ticket per fresh session) has a
short and public history, and the repository records its part in it: the README's "Origins and
pinned provenance" table and [`UPSTREAM.toml`](../../UPSTREAM.toml) pin every borrowed skill to a
commit.

- **The pattern.** In December 2025 Thariq Shihipar of Anthropic described the loop in a post:
  start from a minimal spec, have the agent interview you, then build the spec in a new session.
  Anthropic's [Claude Code best practices](https://code.claude.com/docs/en/best-practices) now give
  it almost word for word: "Interview me until you could write the spec, then write it to SPEC.md",
  then "start a fresh session to build from it", and later review the diff against `SPEC.md`.
- **The skills.** Matt Pocock turned the loop into skills in
  [mattpocock/skills](https://github.com/mattpocock/skills) during 2026. His first PRD (product requirements
  document) skill interviewed the user itself (February); the interview split out as `grill-me`, after Brooks's
  "design tree"; the PRD skill then stopped interviewing (April); and in July the chain became
  `to-spec`, `to-tickets` and `implement`, with tickets as tracer-bullet slices, each "sized to fit
  in a single fresh context window" (a context window is what an agent can hold in one session).
  He credits Brooks's *The Design of Design* (2010) for the design tree and Hunt and Thomas's *The
  Pragmatic Programmer* (1999) for tracer bullets: thin slices that run end to end. Thoughtworks'
  Technology Radar put *grilling* in Trial (its ring for techniques worth trying on a project that
  can absorb the risk) in November 2026, citing his repository.
- **What this repository changed.** Grilling is adapted to offer `/fusion` when rounds stop
  carrying judgement. `adr-spec` merges an earlier local skill with `to-spec`: decisions are
  recorded and approved before the spec, which refuses its scope and seams sections unless a
  grilling or a finished fusion page came first, and the spec is frozen, with dated amendments.
  `tickets` keeps tracer bullets, blocking edges (which ticket must land first) and one-window sizing, but tickets are durable
  files, each proved by a named check, with doneness derived from that check. `implement` is
  rewritten to claim a ticket, load only what it names, prove it by a loop chosen for its kind of
  work, and record what diverged. `tdd` restores the refactor step upstream dropped.
- **The principles.** Lauren Tan's [pstack](https://github.com/cursor/plugins/tree/main/pstack),
  published in Cursor's plugin repository in May 2026, contributed `unslop`, `show-me-your-work`,
  and two principles behind `start-session`: guard the context window, and remove a shared write
  target rather than lock it. pstack itself ships no planning skills ("the best spec is code"),
  and it asks agents never to block on the human: the opposite pole from "the user rules every
  fork".

**What `/fusion` adds to that lineage.** The upstream interview hands the user questions;
`/fusion` draws the model they belong to as a page, with the frame, a rival frame, the forks' stakes
and the edge of the agent's view. Upstream keeps the interview and the spec in one session; a
finished page carries its rulings in a ledger, so the spec can be written in a fresh session after a
resumption check. The page is checked before you see it by a fresh reader, from another model
family where the host offers one; it records several responders by name; and its review scale
compares a spec's intent, commitment and build, with the context then and now, where upstream's
[`to-spec` documentation](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/docs/engineering/to-spec.md) calls the spec a throwaway record.

## The field it belongs to

Writing a spec for an agent to build from has become a practice of its own, usually called
spec-driven development. Its main tools, among them the BMAD Method and Tessl, structure the same arc in different ways:
[GitHub Spec Kit](https://github.com/github/spec-kit) (constitution, specify, plan, tasks,
implement), [Kiro](https://kiro.dev/docs/specs/) (requirements, design, tasks), and
[OpenSpec](https://github.com/Fission-AI/OpenSpec), whose delta specs, archived in dated folders,
are the nearest relative we found to a frozen spec with dated amendments. Geoffrey Huntley's
[Ralph loop](https://ghuntley.com/ralph/) (2025) made the case for a fresh context per task with
the spec as the only memory, and OpenAI's
[Symphony](https://openai.com/index/open-source-codex-orchestration-symphony/) (2026) gives every
unblocked ticket its own agent.

The practice has sharp critics, and `/fusion` is shaped by them:

- Birgitta Böckeler [distinguishes](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
  three levels: spec-first (written before the work), spec-anchored (kept and maintained after it)
  and spec-as-source (the only thing a human edits), and found reviewing generated specs heavier
  than reviewing code (2025). A frozen spec with amendments and a review scale sits between the
  first two.
- François Zaninotto calls it [the waterfall striking back](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)
  (2025), and Gabriella Gonzalez argues that [a sufficiently detailed spec is code](https://haskellforall.com/2026/03/a-sufficiently-detailed-spec-is-code)
  (2026). Hence a spec that holds intent, decisions and acceptance, with design detail sent to a
  contract, a decision record, or nowhere; and pages sized by their subject.
- Thoughtworks' Radar (Vol. 35, November 2026) put *interactive visual plans with agents* in Trial
  beside grilling, and cautioned against *AI-driven documentation sprawl* and *human-in-the-loop
  theater*, "an empty approval step rather than a real check". The answer form's untouched warning
  and the owner's rulings are aimed at the second; the first is a live risk for any spec with
  amendments.

The evidence is young but pointed. In a sample of 266 repositories, Agarwal and colleagues found
that 77.6% of spec files contain implementation detail and 81.5% have a single recorded commit:
specs mix *how* into *what*, and most are committed once
([2026 preprint](https://arxiv.org/abs/2608.25202)). Studies of real agent sessions find
misalignment that users must correct and work reports that overstate success
([Tang et al., 2026](https://arxiv.org/abs/2605.29442);
[Yang et al., 2026](https://arxiv.org/abs/2611.25760)), which is why a review rests on the code
and the checks rather than on the agent's closing note. We found no controlled study that compares
spec-driven work with plain prompting, or that measures planning pages; `/fusion` is a design argued
from these sources, not a measured result.

## Where it sits

![The spec-driven pipeline: /fusion before /deconstruct at project scale and beside grilling before /adr-spec at component scale, the page it leaves, and the review scale reading the pipeline from below.](figures/pipeline.svg)

*Figure 2. Teal marks `/fusion` and its pages; grey, the rest of the pipeline. A plan page comes
before each commitment: before `/deconstruct` writes a project's spec map, and before `/adr-spec`
writes a spec, as the other way in beside grilling. A finished page is committed and cited in the
spec's Anchors (its list of the decisions, contracts and earlier specs it relies on). A
first-component page, for the first spec where nothing is built yet, goes to `/deconstruct` for its
row in the spec map, then to `/adr-spec`. The review scale reads a spec at any stage after
`/adr-spec` and hands its rulings back.*

The rest of the pipeline is described in [`../../docs/sdd-workflow.md`](../../docs/sdd-workflow.md).
Grilling keeps its rule that the interview, the spec and the tickets happen in one unbroken
session. A finished page is the exception: it holds the thinking in a file, so the spec can be
written in a fresh session, after a check that the page's rulings still stand.

## One session

![Four steps the agent takes alone, then rounds with you, then the hand-off, with a loop back from your reaction to the check.](figures/session.svg)

*Figure 3. The agent works alone first: it reads broadly, searches for precedents, passes through
seven lenses and draws the page from a template, which a fresh reader then checks. Then the rounds are together:
you react, and the page is revised and checked again until you call it finished. Then the hand-off
to the next skill.*

The **seven lenses** are the agent's way of not missing a side of the plan: the system it touches
today, its place in time, the principles it must respect, the people it affects, where it will be
proved, how it could fail, and the alternatives, including the smallest version and not building
it. Every lens is run; only the sections that earn their place are drawn.

## The anatomy of a page

![A curve through the sections of a page in reading order, from the whole over time at the top to one decision at the bottom; the forks sit at the lowest point.](figures/altitude.svg)

*Figure 4. The altitude of each section, in reading order. The page climbs to the whole (the zoom
out and the trajectory) before it descends, and it never puts three detailed sections in a row
without first showing the whole they belong to. The forks sit at the lowest point, after the frame,
the alternatives and the edge of the agent's view. The sections that frame the page rather than
argue it (since you last read, the ledger, the terms, the answers, the log) are not drawn.*

The sections in brief: the **thesis**, one sentence on what changes; the **zoom out**, the system
or world the plan sits in; the **trajectory**, what comes before, after and later; the **frame**
and its rival; the **shape**, the parts and the seam where the work will be verified; the
**precedents**; the **alternatives**, including the smallest version and not building it; **where
my view ends**; the **assumptions**, each with what breaks if it is wrong; the **forks**; the
**defaults**; and the **preview** of what the next skill would write.

Under the masthead, which states the scale, a page opens with what moved since you last read,
then a **ledger**: the rulings settled so far with their reasons, the open forks, the
defaults, the assumptions, and a line for each section left out and why. A later session reads the
ledger instead of the whole page. **Terms** come before content, so no abbreviation is used before
it is defined.

**The key.** Every figure uses the same marks, so you learn them once:

| Mark | Means |
|---|---|
| grey, solid | exists today |
| teal, solid | new in this plan |
| ochre, solid | exists, and this plan changes it |
| teal, dotted | planned later, beyond this plan |
| grey, dashed | left out on purpose |
| coral | open, needs you |

**The fork card.** Where the fork sits; the problem in plain words; what is at stake; the options,
each concrete enough to picture; what you hold that makes it yours; the agent's provisional
recommendation, folded, with what would change its mind; and the ruling. "What would change my
mind" is a lever: if you know that fact, you can move the recommendation with it.

**The answer form.** An HTML page lets you answer on the page itself. Each fork starts on the
agent's recommendation, with every other option one click away and a note under each; a fork you
leave untouched keeps it. Defaults
and assumptions have keep or veto. **Gather my answers** writes a plain-text summary marking each
fork *kept* or *changed*, and **Copy** puts it on your clipboard to paste back. Two guards keep
silence from reading as agreement. If you click no fork at all, the summary says so at its top,
and the agent asks before treating the recommendations as rulings. A fork that grants a
permission, such as pushing a branch, starts unanswered. A page is finished only when no fork is
open. A responder name lets the same page go to other people, whose answers are recorded under
their names; when responders disagree, each answer stays on record and the person who rules
decides (in a review, the spec's owner).

## Four scales

![Four panels: a project's set of specs, a product's first component, a component in a system, and a spec already written, each with what its first zoom-out shows and where it hands off.](figures/scales.svg)

*Figure 5. What the first zoom-out shows at each scale. A project page shows the whole problem and
proposes the set of specs (boxes A to F). A first-component page shows the world the first piece enters, where
nothing is built yet. A component page shows the system today with the component placed in it. A
review page shows a spec beside its own records.*

The scale is stated in the masthead, the first thing on the page, and you can correct it like any other part of the
frame. A request to plan the specs means project. No code and no spec map means first component. A
spec-map row or a built module means component. A spec that already exists, named for review,
means review. When two could apply, as with a new product that could start as a project or as its
first component, the agent states its choice and its reason at the top of the page, and the choice
is yours. Every section keeps its job at every scale, and
[`references/scales.md`](references/scales.md) says what each one holds at each.

## Rounds move the picture

![The review frame in its first round: three records, intent, commitment and built, with the drift between them.](figures/records-round1.svg)

![The same frame two rounds later: the records now say what each holds at any stage, and a second row compares the context when planned with the context today.](figures/records-round3.svg)

*Figures 6 and 7. One figure, two rounds apart, from the page that designed the review scale. In
round 1 a review only looked back at built work. Two rounds of answers later it had widened: a
review runs at any stage, so "built" may be nothing; the caller's own words count as intent; and a
second row asks whether the context the spec was planned in has moved. The red lines are the gaps,
called drift, explained under Review; teal marks what the review reads fresh. The figures
illustrate how rounds move a picture; they are not evidence that rounds work.*

A round revises the picture itself, not just the prose around it: the figure and the section a
contribution touches. A ruled fork's card stays on the page, read-only, with its ruling, and the
answer form asks only what is still open. Each contribution is logged with its round and the place
it moved the plan. When the page is finished, the agent writes the closing summary itself from
that log: what you contributed that it had not anticipated, and where it shows.

Where the host keeps every file it shows, each round gets its own copy for viewing. Those copies
are working files and are never committed. The page is committed once, as one file, with the work
it feeds (see Running it), and its read-only cards, its "since you last read" and its log are the
round history.

## Checks

Before you see any version, a fresh agent reads the page alone, with no conversation and no repo,
and from a different model family where the host offers one. It restates every fork in its own
words and lists terms used unexplained, decisions hiding as defaults, claims without anchors, and
figures that contradict the prose. This is a **teach-back**, named after the health-communication
method in which a patient explains back what they were told, to test the explanation rather than
the listener. The agent fixes every miss and renders the page to look at each figure.

The check follows the change. A first draft, and any round that changes the frame, a figure, the
scale, a fork or a default, gets the full teach-back. A round that only records your rulings or
fixes wording gets a focused check of what changed. Every version gets one, and the page says
which. In the same spirit, the web is searched for precedents when a subject or a fork is new to
the repo, and the page says so in a line when the precedents it already holds settle it.

## Review

![Review reads a spec at four stages along the top (drafted or approved, tickets cut, part-built, built) and hands rulings back along the bottom to /adr-spec, /tickets, or a new fusion page.](figures/review-scale.svg)

*Figure 8. A review can start at any stage after `/adr-spec`. Its rulings go back to the skills
that already write those files: `/adr-spec` revises a draft or writes an amendment, `/tickets`
recuts or adds tickets, and a re-plan opens a new fusion page. An accepted finding stays on the
review page, with its reason and a condition for revisiting it. `/implement` builds one ticket per
session, and at the spec's close writes the acceptance record, grading each requirement.*

A review revisits a spec already written: drafted, cut into tickets, part-built or built. It may be
yours, a teammate's, or one sent to an outside expert. It puts three records side by side, as in
Figure 7: what was **intended** (the fusion page's rulings, or the spec's opening sections and its
decision records, plus what the person calling the review says), what was **committed** (the spec
and its amendments, and the tickets if cut), and whatever is **built**. Beside them it sets the
context when the spec was planned against the context today. A spec with nothing built still has
gaps to show, which is why a review is worth running before the build.

The gaps have names. **Spec drift** is between intent and commitment, **build drift** between
commitment and what was built, **intent drift** between intent and what was built, and **context
drift** between the context then and now. Each finding is one of: diverged, missing, unproven, a
surprise nobody planned for, or the context moved. Built work whose tickets are still open is not
yet a finding; a gap between intent and commitment is a finding at any stage. A new intent stated
by anyone other than the owner is itself a finding, for the owner to rule on.

![Three overlapping circles: the author's horizon, the reviewer's and the agent's; the review page sits where all three overlap.](figures/three-horizons.svg)

*Figure 9. A review fuses at least three horizons: the author's, recorded on the fusion page and in
the spec (or in the spec alone, when it had no page); the reviewer's; and the agent's.*

**Who rules.** The spec's owner: the person its Owner field names. When it names no one, the page
asks who owns the spec before anything is ruled. A fresh AI reviewer writes findings onto the page before the owner
reads, each with its evidence and its author, and the reviewers' findings, human and AI, are
evidence under their names. The owner answers every finding, with a reason when declining one.

**What a finding resolves to.**

| Resolution | Written by |
|---|---|
| accept: the gap is real, and the spec stays as it is, with a reason and a condition for revisiting it | the owner, on the review page |
| revise a spec still in draft, or amend an approved one | `/adr-spec` |
| recut the open tickets, or add new ones (a revert is a ticket) | `/tickets` |
| re-plan | a new fusion page |

**When to re-plan.** A horizon does not move by itself when the system changes; it moves when
someone takes in what changed, and that is what a new fusion does. So when a premise of the spec
no longer holds (work would cross its boundary with another component, or a decision it rests on
has been superseded), the old fusion no longer covers the situation, and the review hands over to a
new page. When the premises hold and only scope, inputs and outputs, or acceptance change, the
spec is amended. A review never edits a spec, a decision record or a ticket; it proposes, and the
skills that own those files write them.

## Figures as patterns

Most figures in this document were first drawn on the pages that designed this skill and its
review scale, and the agent uses them again. The
[figure library](references/figures.md) indexes each one as a pattern with a note on when it fits:
a new step in a pipeline, one view at several scales, a process with a loop, records compared with
the drift between them, overlapping views. When a page needs a figure, the agent starts from the
closest pattern and draws its own content. Two more patterns, shown here with invented content:

![One whole turn of a running system along the top, with what a new part adds hung under the stages it touches; one change left out on purpose, dashed; one question open, in coral.](figures/pattern-new-part-in-a-loop.svg)

*Figure 10. A new part in a running loop, shown with an invented order-fulfilment system. Draw one
whole turn of the system first, then hang each thing the new part adds under the stage it touches,
so the reader sees what it does not touch. A record with no effect at runtime hangs under nothing;
a change left out is dashed, and an open question is coral.*

![Four rows, one per pile of a source, with columns for the pile, what it becomes and its effect at runtime; only two piles reach the running system.](figures/pattern-sorting-into-piles.svg)

*Figure 11. Sorting a source into piles by what each becomes, shown with an invented supplier's
catalogue. One row per pile, so the decisive fact can be read straight off the last column: here,
that no pile reaches pricing.*

## Running it

`/fusion` ships in this repository's `sdd` plugin for Claude Code, and as a personal skill for
Claude Code, Codex and other hosts through `bin/link.sh` (see the top-level README's Installing
section). You type it; the agent never starts it on its own. Name what you want planned, as in
`/fusion plan the export of reports to CSV`, or ask for a review, as in `/fusion review spec B.3`. It reads `planning/agent/profile.md` for the paths it
needs: `fusion_dir` for where pages live (by default `planning/fusion/`), and the project's plan,
roadmap, spec map, specs, tickets, decision records, glossary, architecture document and
authority map (which file or person owns the answer to each kind of question). A repo with no
profile still works: the page lists the values it would need.

Pages are named `<date>-<slug>.html` (or `.md` for a plan that is an inventory or a mapping, with
no flow to draw),
and a review page `<date>-<slug>-review.html`. Answer through the page's form, or reply in chat
by ID: "F1: b, because…", "veto D3", or anything that is not on the page. A reframe is worth more
than a ruling.

A finished page is built to be picked up later, by `/adr-spec`, `/deconstruct`, `/tickets` or a
new `/fusion`. That reader runs the **resumption check**: it reads the ledger, compares the facts
the page was checked against with today, lists every premise that changed, and asks whether the
rulings still stand. A page is committed with the spec, spec map, amendment or tickets it feeds,
and once those are approved it is frozen: a record, with later change belonging to the spec's
amendments.

## Precedents and further reading

The sources are grouped by what they are to this skill: where it comes from, the field it works
in, and the older ideas it rests on. The newest is from November 2026.

**Lineage**

- Thariq Shihipar (Anthropic), the interview-then-spec loop, December 2025; now in Anthropic's
  [Claude Code best practices](https://code.claude.com/docs/en/best-practices).
- M. Pocock, [mattpocock/skills](https://github.com/mattpocock/skills), 2026: `grill-me`,
  `to-spec`, `to-tickets`, `implement`; the source of this repository's grilling and ticket skills.
- L. Tan, [pstack](https://github.com/cursor/plugins/tree/main/pstack), Cursor plugins, 2026:
  `unslop`, `show-me-your-work`, and the principles behind `start-session`.
- G. Huntley, "[Ralph Wiggum as a 'software engineer'](https://ghuntley.com/ralph/)", 2025: a
  fresh context per task, with the spec as the only memory.
- F. P. Brooks, *The Design of Design*, 2010; and A. Hunt and D. Thomas, *The Pragmatic
  Programmer*, 1999: the design tree and the tracer bullet, as the upstream credits them.

**The field**

- [GitHub Spec Kit](https://github.com/github/spec-kit), [Kiro specs](https://kiro.dev/docs/specs/)
  and [OpenSpec](https://github.com/Fission-AI/OpenSpec): the main spec-driven development tools.
- B. Böckeler, "[Understanding Spec-Driven-Development](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)",
  2025; F. Zaninotto, "[The Waterfall Strikes Back](https://marmelab.com/blog/2025/11/12/spec-driven-development-waterfall-strikes-back.html)",
  2025; G. Gonzalez, "[A sufficiently detailed spec is code](https://haskellforall.com/2026/03/a-sufficiently-detailed-spec-is-code)",
  2026: the critiques.
- Thoughtworks, [Technology Radar Vol. 35](https://www.thoughtworks.com/radar/techniques),
  November 2026: grilling and interactive visual plans with agents in Trial; documentation sprawl
  and human-in-the-loop theater as cautions.
- Agarwal et al., "[Spec-Driven Development as Prescribed and as Practiced](https://arxiv.org/abs/2608.25202)",
  2026 preprint: how specs are written and how they decay.
- Tang et al., "[How Coding Agents Fail Their Users](https://arxiv.org/abs/2605.29442)", 2026;
  and Yang et al., "[Unfaithful Work Reports by Coding Agents](https://arxiv.org/abs/2611.25760)",
  2026 preprint: why a review rests on evidence, not on the agent's report.
- Kumar et al., "[Plans Work in Mysterious Ways](https://arxiv.org/abs/2607.23670)", VL/HCC
  2026; He et al., "[Plan-Then-Execute](https://arxiv.org/abs/2502.01390)", CHI 2025; and
  Dhanorkar et al., "[Human oversight of agentic systems in practice](https://arxiv.org/abs/2606.05391)",
  2026 preprint: how people plan with agents, when their involvement helps, and how a plan comes
  to stand in for the work it describes.
- Kim et al., "[AIPOM](https://arxiv.org/abs/2509.24826)", 2025: a small pilot comparing plans
  drawn as graphs with plans in text.

**Foundations**

- H.-G. Gadamer, *Truth and Method*, 1960: understanding as a fusion of horizons.
- A. MacLean, R. M. Young, V. Bellotti and T. P. Moran, "Questions, Options, and Criteria:
  Elements of Design Space Analysis", *Human–Computer Interaction*, 1991: design rationale made
  visible as questions, options and the criteria between them, the ancestor of a fork card.
- E. Horvitz, "Principles of Mixed-Initiative User Interfaces", CHI 1999: when an agent should ask
  and when it should act.
- B. J. Grosz and S. Kraus, "Collaborative Plans for Complex Group Action", *Artificial
  Intelligence*, 1996: a shared plan as commitments held by more than one party.
- C. Argyris, "[Double Loop Learning in Organizations](https://hbr.org/1977/09/double-loop-learning-in-organizations)",
  *Harvard Business Review*, 1977: fixing within a frame against questioning the frame; an
  amendment against a re-plan.
- US Army, TC 25-20, *A Leader's Guide to After-Action Reviews*, 1993: what was supposed to happen,
  what happened, why, and what to sustain or improve.
- G. C. Murphy, D. Notkin and K. Sullivan, "[Software Reflexion Models](https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html)",
  1995: comparing an intended model with what was built, as convergences, divergences and absences.
- R. Kazman, M. Klein and P. Clements, [ATAM](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/),
  SEI, 2000: evaluating an architecture before it is built, and re-justifying a judgement when its
  assumptions change.
- M. Nygard, "[Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)",
  2011: a reversed decision is kept and marked superseded.
- M. E. Fagan, "[Design and code inspections to reduce errors in program development](https://www.ida.liu.se/~TDDC90/labs/lab-papers/fagan76.pdf)",
  1976; Atlassian, "[DACI](https://www.atlassian.com/team-playbook/plays/daci)"; and
  [RFC 7282](https://www.rfc-editor.org/rfc/rfc7282), 2014: reviewers find and argue, one named
  decider rules, and every issue is addressed even when it is not accommodated.
- G. Klein, "[Performing a Project Premortem](https://hbr.org/2007/09/performing-a-project-premortem)",
  *Harvard Business Review*, 2007: reviewing a plan before it starts.
- E. J. Johnson and D. Goldstein, "[Do Defaults Save Lives?](https://doi.org/10.1126/science.1091721)",
  *Science*, 2003; and Z. Buçinca, M. B. Malaya and K. Z. Gajos,
  "[To Trust or to Think](https://arxiv.org/abs/2102.09692)", 2021: a pre-set option pulls like a
  recommendation, and designs that make people decide before they accept reduce over-reliance on
  AI, at some cost in comfort. They motivate the form's warning when nothing was clicked; its own
  effect has not been measured.
- AHRQ, "[Use the Teach-Back Method](https://www.ahrq.gov/health-literacy/improve/precautions/tool5.html)";
  and R. Wilsenach, "[Ship / Show / Ask](https://martinfowler.com/articles/ship-show-ask.html)",
  2021: check the explanation, every time, in proportion to how new and risky the change is.
