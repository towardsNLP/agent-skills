# Anatomy of a fusion page

What each section is for. What each one shows at each scale is in [`scales.md`](scales.md).

## Sections, in reading order

The id is the element id in [`page.html`](page.html); the name is the heading in
[`page.md`](page.md). Altitude alternates on purpose, so the reader never meets three detail
sections in a row without first seeing the whole they belong to. The forks sit at the lowest
point, after the whole, the frame, the alternatives and the edge of your view.

| id | Section | Altitude | Asks of you | Invites from the user |
|---|---|---|---|---|
| `thesis` | Thesis | middle | one sentence on what changes, in the masthead with the scale, the round, and "facts checked against" | "is that the change I want?" |
| `since` | Since you last read | — | what moved since their last round, by kind: boundary, dependency, sequence, acceptance check, frame, fork | — |
| `ledger` | Ledger | — | settled rulings with reasons, open forks, defaults, assumptions, sections left out and why | — |
| `terms` | Terms | — | every abbreviation and project term, before its first use | — |
| `zoom-out` | Zoom out | high | the system today, the world the plan enters, or the whole problem, in the key's colours | "it also touches X" |
| `trajectory` | Trajectory | highest | before, after and later; what it unlocks and rules out; its place on the roadmap | "do Y first" |
| `frame` | Frame | middle | the cut you chose and why, and at least one rival frame with what the plan becomes under it | a reframe, the most valuable answer |
| `shape` | Shape | low | parts, inputs and outputs, the flow, and the seam where it is verified | "this part is really two" |
| `precedents` | Precedents | high | similar situations in the repo and on the web: each with its source, date and what it suggests for this plan | "we tried that in X, and it failed because …" |
| `alternatives` | Alternatives | high | two to four genuinely different shapes, the smallest version and not building it, each with a cost and a gain | bring back one you rejected |
| `edge` | Where my view ends | middle | the facts only the user holds: history, people, commitments, intent | the facts only they hold |
| `assumptions` | Assumptions | low | numbered, each with what breaks if it is wrong and how to check it | "A3 is false" |
| `forks` | Forks | lowest | the decisions that need the user, in the fork card below | rulings |
| `defaults` | Defaults | low | the decisions that need nothing only the user holds, listed for veto | a veto |
| `preview` | What the next skill would write | middle | spec-map rows, or the spec's IN, OUT, seams and ADR candidates, and a rough ticket count | catch a consequence early |
| `answers` | Your answers | — | the answer form's gather and copy controls, and the responder name | the gathered answers, pasted back |
| `contributions` | Contributions by round | — | each contribution of the user, its round, and the anchor where it moved the plan; each check that ran | — |
| `anchors` | Anchors | — | the files, commits and documents the page stands on | — |

A section that does not earn its place is left out, and the ledger says so in one line.

## The key

Every figure uses the same marks, so a reader learns them once:

| Mark | Means |
|---|---|
| grey, solid | exists today |
| teal, solid | new in this plan |
| ochre, solid | exists, and this plan changes it |
| teal, dotted | planned later, beyond this plan |
| grey, dashed | left out on purpose |
| coral | open, needs the user |

At project scale the specs are the plan itself, so they are solid teal. Add a second key only for
a distinction the project already draws, such as where a model decides and where code decides.

## The fork card

| Field | Holds |
|---|---|
| **Where** | the figure or section the fork belongs to |
| **Problem** | the decision in plain words, before any file or line |
| **At stake** | the moment in a concrete case where the options produce different outcomes; what that changes in the spec, the ADRs and the tickets; the cost to reverse |
| **Options** | lettered (a), (b), (c), each concrete enough to picture |
| **Needs you** | what the user holds that makes this theirs: history, people, intent, taste |
| **Provisional recommendation** | the recommended option pre-selected in the answer form; the reasoning folded under "Show my provisional recommendation", with what would change your mind; the summary marks whether the user kept or changed it |
| **Ruling** | open, or the user's answer with its round and reason |

"What would change my mind" is a lever: a user who knows that fact can move the recommendation
with it. A question whose "needs you" field stays empty is a default, not a fork.

## Rounds

A revision moves the picture itself: the figure and the section a contribution touches. The
**since you last read** box and the contribution log point at what moved, so a re-read costs
minutes. A ruled fork's card stays on the page, read-only, with its ruling and round; the answer
form carries only open questions, and it closes when the page is finished. When the host keeps every file it shows, write each round to its own copy (`-r1`,
`-r2`); the highest is current. The page committed at the finish is one file without the suffix, and that file is the one a later session reads.
