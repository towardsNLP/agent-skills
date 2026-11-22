# Figure library

Figures that carried real pages, kept as patterns. When a section of a page can be drawn, start
from the pattern closest to what the section must show: take its structure, its use of the key and
its layout, and draw your own content. Never reuse a pattern's labels. They describe the page the
pattern came from, or an invented example.

Each file in [`../figures/`](../figures/) is a standalone SVG with the key's colours, a dark variant
and a background card inside it, so it also renders on its own. On a page, copy the drawing without
the file's `<style>` and background card: the page's own classes (`bx-exists`, `bx-new`,
`bx-changed`, `bx-later`, `bx-out`, `ar`, `ahp`, `t`, `st`) already carry the key. A pattern that
uses a helper the template lacks (`ar-new`, `ahn`, `brk`, `doc`, `dot`, `gl`, `region`, `wave`,
`halo`, `bx-open`) needs that one rule copied from the file's `<style>` into the page's. Give every
marker a unique id per figure.

| Pattern | Use it when | File |
|---|---|---|
| A new step in a pipeline | the plan adds or changes a stage in a flow that exists: grey for today, teal for new, ochre for changed, and the artefact the new step leaves | [`pipeline.svg`](../figures/pipeline.svg) |
| One view at several scales | the same first view looks different at different sizes, and the reader must see which one this plan is | [`scales.svg`](../figures/scales.svg) |
| A process with a loop | work runs through steps, and a loop back is what makes it a process; brackets name who does which stretch | [`session.svg`](../figures/session.svg) |
| A new part in a running loop | the plan adds a part to a cycle that already runs: draw one whole turn, hang what the part adds under the stage it touches, dash what is left out, and mark what is open in coral | [`pattern-new-part-in-a-loop.svg`](../figures/pattern-new-part-in-a-loop.svg) |
| Sorting into piles | a source (a document, a dataset, a backlog) must be triaged: one row per pile, with columns for the pile, what it becomes and its effect, so the reader sees which pile reaches what | [`pattern-sorting-into-piles.svg`](../figures/pattern-sorting-into-piles.svg) |
| Reading at several points, handing back | a step reads a flow at several stages and sends its results back to different places: reads along the top, hand-backs along the bottom, so no line crosses | [`review-scale.svg`](../figures/review-scale.svg) |
| Records compared, with the drift between them | the plan compares versions of one thing (meant, promised, built; then and now), and each gap is a finding | [`records-round3.svg`](../figures/records-round3.svg) |
| Overlapping views | two or three people see the same subject from different standpoints, and what the page holds is where they overlap | [`two-horizons.svg`](../figures/two-horizons.svg), [`three-horizons.svg`](../figures/three-horizons.svg) |

Two files are not patterns. [`altitude.svg`](../figures/altitude.svg) draws the page's own reading
order, and [`records-round1.svg`](../figures/records-round1.svg) is the first round of
`records-round3.svg`, kept so the explainer can show a figure revised by a user's answers. Both
are drawn for [`../README.md`](../README.md).
