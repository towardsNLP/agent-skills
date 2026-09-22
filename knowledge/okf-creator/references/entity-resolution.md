# Entity resolution playbook

Entity resolution is a **problem of reference** (read `sense-and-reference.md`): it
decides which distinct *senses* (surface forms) designate the same *object*, and
records the informative identity `a = b`. The tool you must NOT use to make that
decision is *sense*-similarity — string overlap or embedding proximity — because
sense proximity does not settle reference identity. "Apple" the company sits right
on top of "apple" the fruit in string/sense-space and is a different object in
reference. Resolution is a curated reference judgment, not a clustering output.

When a source field holds free-text entities — author names, place names, product
names, org names, free tags — you must resolve variants to canonical concepts before
they become graph nodes. Any real knowledge-graph build has this step. The two
failure modes are equal and opposite, and both are easy to fall into.

## The two failure modes

1. **Too granular / naive.** One node per raw string. You get hundreds of singletons
   (a product field full of one-off SKUs; an author field where `J. Smith` appears
   once) that each link to one entity and add nothing as nodes. Pure noise.
2. **Too coarse / over-clustered.** You collapse everything into a handful of broad
   buckets and destroy the query the user actually wanted — "which services use
   **PostgreSQL**" dissolves into a generic "databases" bucket; "books by **this
   author**" dissolves into "20th-century writers". A vague classification is not
   insight.

The right granularity is **whatever the query needs**, and it is a decision the
user should make, not one you should silently pick.

## Naive string clustering is wrong — prove it to yourself first

Before proposing any merge strategy, look at the data. Substring/keyword clustering
mis-merges: `Apple Inc.` is NOT `apple` (the fruit); `Java` (the language) is NOT
`Java` (the island); `Paris, France` is NOT `Paris, Texas` despite sharing "Paris".
And string normalization alone barely dedupes a messy field. Real resolution needs
*reference judgment*, which means it cannot be a pure black box — it needs a curated,
auditable map the user owns.

## The method

**Layer 1 — deterministic normalization.** Case, whitespace, ampersand, plural fold
(`Datasets` = `Dataset`, `libraries` → `library`). Merges only unambiguous trivial
sense-variants. Safe, no reference judgment.

**Layer 2 — a curated canonical map** (a YAML the user owns and audits). Two shapes,
pick per the granularity decision:
- **Synonym map** (keep specific entities): merge only true co-references
  (`NYC` = `New York City` = `New York, NY`), keep `PostgreSQL` its own node. Pair
  with a frequency **threshold** (§below) to prune singletons.
- **Category map** (coarse, matchable): map raw strings into a controlled ~20–40
  concept vocabulary via keyword rules + overrides for the ambiguous cases. Anchor
  to a real standard where one exists (an industry classification, a subject
  taxonomy, a genre list) rather than inventing categories.

**Layer 3 — a review-candidates file.** Everything unmapped (or that fell to
"other") goes to `*_review_candidates.csv`, ranked by frequency, as the user's
curation queue. Never silently drop; the raw string always stays in the entity's
*body* even when it doesn't earn a node, so no retrieval context is lost.

## The frequency threshold (for the synonym/specific approach)

Keep a node only when a canonical entity aggregates **≥ K** other entities
(K=3 is a good default; expose it as a constant). This prunes singletons while
keeping every entity that connects enough to be worth querying. Compute and *show
the user the distribution* at K=2/3/5 so they choose — coverage vs. node count is
their tradeoff, not yours.

```
# illustrative — resolving a messy free-text field of ~1,100 raw values:
K >= 1  -> 1102 nodes | 900/900 entities keep a node   (too granular)
K >= 3  ->  313 nodes | 774/900                         (good default)
K >= 5  ->  151 nodes | 699/900                         (coarser)
```

## Keyword matching gotchas (for the category approach)

- Match keyword **stems on a word boundary** (`\bfarm` catches farming/farms) but
  make **short keywords full words** — `\bpub\b`, not `\bpub`, or "pub" matches
  "public" and mis-tags everything. This class of bug is subtle; test it.
- Order sectors specific → general (first match wins), and keep explicit
  `overrides` for the compound/ambiguous strings.

## The rule that ties it together

Whatever you choose, the raw source value survives in the entity body (LLM context)
regardless of whether it becomes a node; the node layer is a *query/matching*
convenience, gated by the granularity decision; and every merge/drop is auditable in
the canonical map + review file. Curation is the user's; the machinery is yours.
