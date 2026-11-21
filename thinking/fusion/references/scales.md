# Scales

Every section keeps its job at every scale. This table shows what each one holds when the plan is
a set of specs, a product's first component, or a component in a system that exists. The biggest
difference is the first zoom-out: there is not always a system to place the plan in.

| Section | Project: a set of specs | First component: nothing built yet | Component: in a system |
|---|---|---|---|
| **Zoom out** | the whole problem: the needs, the people, and what already exists | the world it enters: who does this today and how, the tools and limits around it, and a sketch of the system to come | the system today, with the component placed in it |
| **Trajectory** | the order of work: what unblocks what, and which specs can start first | what this first piece makes possible next, and what it must keep open | before, after, later |
| **Frame** | the cutting principle (by need, by structure, by source, by layer, by user outcome) and the rival cut | the product's first principles; a first component often yields the project's first ADRs | the taxonomy the component is argued in |
| **Shape** | the component map: each component's kind (build, experiment, knowledge revision), its blocking edges, and what it needs from outside (a decision, data, evidence, vocabulary) | the thinnest version that proves the principles end to end | parts, flow, and the seam where it is verified |
| **Alternatives** | other ways to cut the same problem | other first slices: the thinnest end-to-end path, the riskiest part first, the most valuable part first | other shapes for the same component |
| **Where my view ends** | priorities, deadlines, who works on what | the largest at this scale: users, intent, market. Most of the horizon is the user's | history, people, commitments |
| **Forks** | boundaries ("one spec or two?"), granularity, order, what to cut | which piece first, which principles, what it must keep open | design decisions |
| **Terms** | double as `/deconstruct`'s vocabulary check: each term marked settled or proposed; proposed ones go to `domain-modeling` | proposed terms go to `domain-modeling` | terms the reader needs |
| **Grounded in** | the plan, the roadmap, and the code at a commit if there is any | documents, research and conversations, each dated, because there is no code yet | the code at a commit |
| **Preview of** | the spec map's rows | the spec, and its first ADRs | the spec, or the amendment |
| **Hands off to** | `/deconstruct` | `/deconstruct` for its spec-map row, then `/adr-spec`; or a project page first | `/adr-spec` |

## Choosing the scale

- The user names a spec-map row or something already built: **component**. An amendment to a
  frozen spec is a component page whose zoom-out includes the spec as agreed.
- The user asks to plan the specs: **project**.
- No code and no spec map: **first component**. A *project* here is any body of work big enough to
  split into several specs; a *product's first component* is the first spec in a repo where
  nothing is built yet. A new product can start at either scale, and that choice is the user's.

## How the scales chain

A project page hands its component list to `/deconstruct`. Each spec-map row then gets its own
component page, or a grilling when its forks are few and local. That page cites the project page
and carries its boundary rulings as settled.

A first-component page enters before any spec map exists, so `/deconstruct` registers its row
(kind and parent) before `/adr-spec` writes the spec. When its sketch
of the eventual system shows several components with real dependencies, it puts a project page
to the user as a fork, because the order of work is then the bigger decision. If they take it,
the first-component page is kept, marked "continued at project scale", and its world and sketch
become the project page's zoom-out.
