# Spec map skeleton

`spec_map_path` holds **the planned set and nothing else.** One row per component, written by a
human decision and amended by one. Status, counts and progress are computed by
`ticket_status_command` and never written here.

```markdown
# Spec map

The set of specs this project needs, and what gates what. Planned set only — run
`<ticket_status_command>` for what actually exists.

**Last revised:** YYYY-MM-DD

## Components

| ID | Kind | Covers | Blocked by | Requires |
|---|---|---|---|---|
| F1 | build | <the need or component, one line> | — | decision: architecture approved |
| F2 | knowledge-revision | <...> | F1 | ontology: competency questions |
| B1 | experiment | <...> | F1, F2 | data: evaluation set; evidence: baseline run |

## Needs not yet covered

<!-- A need with no component is unbuilt scope. Empty is the goal; omit the section when it is. -->

- <need> — no component yet, raised YYYY-MM-DD

## Vocabulary gaps

<!-- Terms the plan turns on that the glossary does not settle. Hand to domain-modeling. -->

- `<term>` — used two ways in <document>
```

## Reading it

**Covers** is one line. If a component needs a paragraph to describe, it is two components, or it
is not understood yet.

**Blocked by** makes the set a graph. The specs with no blockers are where `/adr-spec` starts. A
cycle means a boundary is in the wrong place — fix the boundary rather than breaking the cycle by
hand.

**Kind** is `build`, `experiment` or `knowledge-revision`. It selects the downstream proof loop.

**Requires** names external prerequisites using `decision:`, `data:`, `evidence:` or `ontology:`.
These do not become fake component IDs merely to make the graph look uniform.

**Needs not yet covered** is the section that earns the document. A component list alone cannot
tell you what is missing; a need with no component can.

## What never goes in here

Which specs are written, which have tickets, which are green, how many of how many. All of it is
on disk already, and a second copy is a copy that goes stale. `ticket_status_command` joins this
map against `spec_dir` and `ticket_dir` and reports the gaps — including a planned component with
no spec, and a spec with no tickets.
