---
name: fusion
description: "Co-plan with the user before a spec or a spec map. Draw the plan as a page they think with (where it sits, the frame, the alternatives, what you cannot see, the forks), revise it in rounds until they call it finished, then hand it to /deconstruct or /adr-spec."
disable-model-invocation: true
---

# Fusion of horizons

Understanding is a **fusion of horizons**. Neither view is erased, and neither is copied. You
see from the code and the documents; the user sees from the product, the people and the
history. The plan comes out of where the two overlap. A grilling hands the user decisions. A
**fusion page** hands them the model those decisions belong to, so they can change the frame
instead of only choosing inside it.

Read `planning/agent/profile.md` for `fusion_dir`, `plan_path`, `roadmap_path`,
`spec_map_path`, `spec_dir`, `decision_records`, `glossary_path`, `architecture_doc_path`,
`constraints_doc` and `authority_map`. Pages live in `fusion_dir` (default `planning/fusion/`),
one per plan, named `<YYYY-MM-DD>-<slug>.html` or `.md`. A repo with no profile yet gets the
default, and the page lists the profile values it needs for the user to set.

## Step 1 — Settle the scale

A plan has one of three scales, and the scale changes what every section shows
([`references/scales.md`](references/scales.md)):

| Scale | The plan is | Zoom out shows | Hands off to |
|---|---|---|---|
| **project** | a set of specs | the whole problem, and what already exists | `/deconstruct` |
| **first component** | the first spec where nothing is built yet | the world it enters: people, today's practice, tools, limits | `/deconstruct` for its spec-map row, then `/adr-spec` |
| **component** | one spec in a system that exists, or an amendment to one | the system today, with the component placed in it | `/adr-spec` |

A spec-map row or a built module named by the user means component. A request to plan the specs
means project. No code and no spec map means first component. When a first-component page's
sketch of the eventual system shows several components with real dependencies, put a project
page first to the user as a fork on that page.

Done when the masthead states the scale and its one-line reason. The user corrects it like any
other part of the frame.

## Step 2 — Read broadly, search for precedents, then pass through the seven lenses

Finding facts is your job. Use helper agents where the harness offers them, and retrieve any fact
you can before asking the user for it.

**Search for precedents in the repo and on the web.** In the repo: earlier specs, decision
records, plans and modules that faced a similar situation, and what they chose. On the web:
how others have solved the same kind of problem, from primary sources such as papers, official
documentation and well-known engineering write-ups. Send the searches to helper agents in
parallel where the harness allows, and keep each precedent to what it is, where it comes from
(path or link, with date) and what it suggests for this plan. A precedent informs the frame and the
alternatives; it never decides a fork. When the harness has no web access, say so on the page.

**Search the web when the subject, or a fork, is new to the repo.** Search depth follows novelty,
not size. A later round that opens no new subject and no new fork searches nothing new, and the
page says in one line that the precedents it already holds settle it.

**A helper's report counts once its work exists.** Before using a helper's findings, check that the
files it was asked to write are there and complete. A helper that delegates collects its own readers'
results before it reports; one that hands back early is resumed or its work rerun, never trusted on
its summary alone.

Then think through every lens, at every scale:

1. **System** — what the plan touches today, at `file:line` and a commit, or in dated documents
   where there is no code.
2. **Time** — its place on the roadmap, what must come first, what it unlocks and rules out.
3. **Principle** — the project's architecture document and constraints. With none, the
   principles this plan would set.
4. **People** — who decides, builds, reviews and is affected, from the authority map.
5. **Proof** — where the work gets verified: the seam, named before any check exists.
6. **Failure** — a pre-mortem. Months later, this has failed. Why?
7. **Alternatives** — at least two genuinely different shapes, the smallest version, and not
   building it.

Done when every lens has a written finding, every claim about what exists carries an anchor, and
each precedent carries its source.

## Step 3 — Draw the page

Start from [`references/page.html`](references/page.html) when there is a flow or an
architecture to draw, and from [`references/page.md`](references/page.md) when the plan is a
mapping or an inventory. [`references/anatomy.md`](references/anatomy.md) gives each section's
job and altitude, the key, and the fork card. Every page carries:

- **A ledger at the top**, under the masthead and "since you last read": settled rulings with
  their reasons, open forks, defaults, assumptions, and one line for each section left out and why.
  A fresh session reads the ledger instead of the whole page.
- **Terms before content**: every abbreviation and project term, defined before its first use in
  the sections. The masthead, "since you last read" and the ledger use plain words and IDs.
- **A frame the user can challenge**: the cut you chose, why, and at least one rival frame with
  what the plan would look like under it. Their most valuable answer may be a frame you did not
  offer.
- **Grounding**: the masthead's "facts checked against" names the commit or the dated documents.
  Every anchor is something a fresh session can open: a committed path, a commit, or a public link.
  Working notes that will not be committed are summarised on the page itself, with their sources.
- **Precedents**: the similar situations found in the repo and on the web, each with its source
  and what it suggests, set beside the alternatives they inform.
- **Pictures that carry the argument**: the page is a visual co-thinking tool. Draw the zoom-out,
  the shape, and each fork's divergence as figures in the page's key, so the reader sees the
  structure before reading about it. A section that can be drawn is drawn.
- **Forks in the card format**: where it sits; the problem in plain words; **at stake**, meaning
  the moment in a concrete case where the options produce different outcomes, what that changes
  in the spec, the ADRs and the tickets, and the cost to reverse; the options; what the user
  holds that makes it theirs; your **recommended option, pre-selected** in the answer form, with
  the reasoning folded and what would change your mind; the ruling.
- **Defaults instead of questions**: a decision that needs nothing only the user holds becomes a
  default they can veto.
- **Where my view ends**: the facts only the user holds, asked as questions they may skip.
- **The preview**: what the next skill would write, whether spec-map rows or a spec's IN, OUT,
  seams and ADR candidates.

The subject decides the size. A first component may need one drawing of today's workflow and one
consequential fork; a project may need several views. Every lens is run, and only sections that
earn their place are shown.

**The answer form.** An HTML page lets the user answer on the page itself: each fork's options as
choices with your recommendation pre-selected and the others one click away, a note under each;
keep or veto for each default and assumption; a text box for each question at the edge of your
view, and one for anything not on the page. A responder name lets the page be shared with other
people for their feedback. **Gather my answers** writes a plain-text summary that marks every fork
as *kept the recommendation* or *changed*, lists only changed defaults and assumptions and every
note, and counts what is still unanswered; **Copy to clipboard** copies it for the user to paste
back. When no fork was clicked, the summary opens by saying so: ask whether the recommendations
stand before recording them as rulings. Answers autosave in the browser. The template carries all of this; a Markdown page is
answered by ID in the reply instead.

Done when every fork has every card field, every figure uses the page's key, and the ledger
names each section left out.

## Step 4 — Teach-back

Before the user sees any version, give a fresh helper agent the page alone: no conversation, no
repo, and a different model family where the harness offers one. It restates each fork in its
own words: what is decided, what each option changes, which it would pick. It also lists terms
used unexplained, decisions hiding as defaults, claims without anchors, and figures that
contradict the prose. Fix every miss. Render the page in a browser where one is available and
look at every figure.

**The check follows the change.** Run the full teach-back on a first draft, and on any round that
changes the frame, a figure or the scale, or adds or changes a fork or a default; a ruling that
moves a figure counts. A round that only records the user's rulings or fixes wording gets a
focused check: a fresh reader restates the changed cards, the ledger and **since you last read**.
Every version gets one of the two, and the contribution log names which.

A check that cannot run is recorded on the page as skipped. With no helper agent, make a
separate pass that reads only the page, and record it as a self-check.

Done when the check restates every fork it covers correctly and the page's contribution log
records which check ran.

## Step 5 — Show it and ask for reactions

Show the page inline where the host displays HTML; otherwise give its path. Ask for reactions,
not approval: a reframe, a broken assumption, a missing part, rulings by ID, anything that is not
on the page. Then wait.

## Step 6 — Revise in rounds

Each reply changes the picture:

- Revise the same sketch: the figure and the section the contribution touches.
- Open the page with **since you last read**, naming what moved by kind: boundary, dependency,
  sequence, acceptance check, frame, fork.
- Record each contribution in the **contribution log**: what the user said, the round, and the
  anchor where it moved the plan. Answers from other people who were sent the page are recorded
  under their names.
- A ruled fork becomes a ruling with its reason, and its card turns read-only: the options stay as
  plain text, the ruling replaces the choice, and the answer form asks only what is still open. New
  forks surface as old ones settle. Carry settled precedent forward as a default.
- Small, local forks may go to a quick `grilling` round asked against the page, with each
  recommendation held back until the user has answered.
- Run the check again before showing, full or focused as step 4 decides.

**Round copies are working files.** Where the host keeps every file it shows, write each round to
its own copy (`-r1`, `-r2`) for viewing; the highest is current. Never commit these copies. The
page committed at the finish is one file per plan in `fusion_dir`, without the suffix, and its
read-only fork cards, **since you last read** and contribution log are the round history. A round
that must be kept is committed to that same path, so git history holds it, never as a separate
file.

The rounds end when the user calls the page finished, no fork is open, and, at the component
scales, the page shows the scope boundary and the proposed proof. Ask the closing question of
step 7 and record the answer, then mark the page finished with the date and close the answer form,
leaving a line that says a later round reopens it. A finished page reopens
only through the resumption check below. Once what it feeds is approved, the page is frozen: a
record, with later change belonging to the spec's amendments. A project page freezes with its spec
map, and a component page with its spec. A first-component page feeds both, so it freezes only
when its spec is approved. The spec map cites it at the commit the map approved, and a later round
that changes a ruling the row relied on goes back to `/deconstruct`, which puts the row to the user
again and cites the page's new commit.

## Step 7 — Hand off

- **Project scale** goes to `/deconstruct`.
- **Component scale** goes to `/adr-spec`.
- **First-component scale** goes to `/deconstruct` first, which registers the component's
  spec-map row with its kind and parent, and then to `/adr-spec`, which takes both from that row.
- The user types each command; give it to them exactly.
- The closing question, asked before the page is marked finished: *what did you contribute that I
  had not anticipated, and where can you see its effect on the plan?* Record the answer in the
  contribution log.
- The page is committed with the PR of the spec or spec map it feeds. A spec cites it in its
  Anchors, or in its amendment entry; a spec map names it in its opening lines.

## Resuming a finished page

A finished page is built to be picked up in a fresh session, by `/adr-spec`, `/deconstruct` or a
later `/fusion`. That reader runs the **resumption check**: read the ledger; compare the page's
"facts checked against" with the current state and list every premise that changed; put the
rulings to the user with those changes and ask whether they still stand. A ruling the user
changes reopens the page as a new round, which is possible until the page is frozen (step 6).

## Hard rules

- **The user rules every fork.** Your recommendation is a pre-selected default they can change in
  one click, and the gathered answers show which defaults they kept and which they changed. A
  summary with no fork clicked is confirmed in chat before it becomes rulings.
- **Facts are yours; decisions are theirs.**
- **Write only the page.** Specs, ADRs, glossary terms and spec-map rows are proposed on it and
  written by `/adr-spec`, `domain-modeling` and `/deconstruct`.
- **Every version passes a teach-back before the user reads it**, full or focused by step 4's
  triggers, or the page says why it could not.
