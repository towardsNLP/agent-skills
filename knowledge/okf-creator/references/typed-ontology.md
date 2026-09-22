# The typed-ontology layer (the value you add on top of OKF)

Vanilla OKF is untyped and schema-less. A catalog becomes a *knowledge graph* only
when you add a governed vocabulary and enforce it. This layer is the moat: the
editorial judgment about what entities exist and how they relate is the thing a
competitor scraping the same public data with plain RAG cannot reproduce. "Insight
= traversal, not hairball" — the relationship layer is the value, so invest in it.

Keep the whole vocabulary in ONE file (`vocabulary.py`) shared by every ingester
and the validator, so a type/predicate/tag is defined once and enforced everywhere.

## 1. Governed types

Each `type` value is a concept kind, and each carries the extra frontmatter it
requires. Example shape:

```python
# Examples span domains — pick types that fit YOUR sources:
TYPES = {
    "Dataset":   ["schema", "owner"],        # a data/analytics catalog
    "Author":    [],                          # a bibliographic catalog
    "Compound":  ["formula", "cas_number"],   # a chemistry knowledge base
    "Service":   ["language", "repo"],        # a software system map
    "City":      ["region"],                  # a geographic catalog
}
RESOURCE_REQUIRED = {"Dataset", "Compound"}  # regulated/official -> need resource:
```

A type not in `TYPES` is rejected by the validator. `RESOURCE_REQUIRED` names the
types whose facts are regulated/official and therefore MUST carry a `resource:`
(official source URI). This is how you stop unsourced facts from creeping in.

## 2. Typed predicates (the queryable edges)

OKF links are untyped; you add typed edges in a frontmatter `relations:` block:

```yaml
relations:
  - {predicate: authored_by, target: authors/ada-lovelace}
  - {predicate: depends_on,  target: services/auth-api}
  - {predicate: located_in,  target: regions/pacific-northwest}
```

Define the allowed predicates with their inverses. Prefer a small, reusable set:
- **Hierarchy:** `broader` / `narrower` (SKOS-style), or `in_category` / `has_member`.
- **Place:** `located_in` / `contains`.
- **Domain edges** (examples across domains): `authored_by` / `authored`,
  `depends_on` / `required_by`, `cites` / `cited_by`, `joins_to` (a data catalog),
  `synthesized_from` (chemistry), `related_to` (generic fallback).

The validator checks every predicate is in the set and every target resolves to a
real entry (file, or folder with an `index.md`). Broken typed edges are bugs, not
tolerated (unlike OKF's tolerant prose links).

Edge direction tip: put the edge where the source expresses it, and answer the
reverse query by scanning incoming edges — e.g., an author node answers "what did
they write?" via incoming `authored_by` edges, exactly like a region node answers
"what's here?" via incoming `located_in`. You rarely need both directions stored.

## 3. Governed tags

A controlled base list plus a few generative patterns (e.g. `level-[0-5]`, or
`year-\d{4}`), plus slugs the catalog derives from its own structure (category or
region names). New tags require a vocabulary change, never ad-hoc invention —
otherwise tags stop being a reliable facet.

```python
def tag_allowed(tag, dynamic):
    return tag in BASE_TAGS or tag in dynamic or any(p.match(tag) for p in TAG_PATTERNS)
```

## 4. Provenance & authority layers

Distinguish, per entry, where its facts come from — and restrict which types may
use which layer:
- **Official** (regulators, standards bodies, the computation engine) — the only
  allowed source for regulated facts (rules, codes, verdicts-criteria).
- **Editorial** (a curated internal source the user provides) — the spine: curated
  lists, descriptions, sequences.
- **Encyclopedic** (background/structure) — must pass the curation gate; never for
  regulated facts.
- **Freshness** (live search) — volatile values (prices, cutoffs); cited +
  `timestamp`ed + marked `freshness_sensitive`; never hand-stored.

The **curation gate**: generated entries land as *proposals* (a PR / a review file),
not straight to trusted, until provenance is confirmed and the source-layer is
allowed for the type.

## 5. The category-as-concept pattern

A classification category is itself a real concept, not just a folder name. Realize
it as the folder's `index.md` (frontmatter + body + member list), with members
linking up via `in_category` and the category linking down via `has_member` (or the
`broader`/`narrower` pair). This makes the hierarchy navigable in both directions.

## The root `index.md` carries the vocabulary

Put the governed types, predicates, and tag rules into the bundle's root `index.md`
so the vocabulary is browsable by an agent *inside* the bundle, not only in your
head. The vocabulary lives in three places that must agree: this `vocabulary.py`
(machine copy + enforcement), the root `index.md` (agent-browsable copy), and the
spec/doc (human rationale). Do not invent a separate `ontology/` folder — real OKF
bundles have none.
