---
name: okf-creator
description: >-
  Build high-quality Open Knowledge Format (OKF) catalogs from real authoritative
  sources — a curated, typed knowledge layer of markdown + YAML for grounding LLMs
  and agents. Use this whenever the user wants to author, structure, build, or
  improve an OKF catalog/bundle, a curated knowledge base or knowledge graph over
  their real assets (data dictionaries, product/bibliographic/scientific/policy
  catalogs, service maps, docs, APIs, YAML/CSV rule sets), convert sources into
  agent-ready knowledge, or set up
  markdown-based knowledge for retrieval — even if they don't say "OKF" explicitly.
  Encodes the content-richness, entity-resolution, source-mirroring, typed-ontology,
  and validation practices that separate a useful knowledge graph from an empty
  folder structure. Reach for it before writing the first entry, not after.
---

# OKF Creator

Build an OKF catalog that is actually *insightful* — a curated, typed, provenance-
tracked knowledge layer over real assets — instead of an empty folder tree of
thin stubs. This skill encodes a specific philosophy of knowledge modeling and the
practices that follow from it.

**Provenance of this skill:** the OKF *format* facts come only from the official
Google spec (`GoogleCloudPlatform/knowledge-catalog`). The *methodology* — the
philosophy below, the typed-ontology layer, the entity-resolution playbook, the
content-richness discipline, the pitfalls, the scripts — is original, distilled from
real builds. It does not follow any third-party OKF toolkit.

## What OKF is (in one breath)

OKF (Google Cloud, v0.1, 2026) is a portable convention: a directory of markdown
files, one per concept, each with YAML frontmatter whose only required field is
`type`. Links between files are plain markdown. `index.md` navigates a folder;
`log.md` records changes. That is the whole format — deliberately minimal (untyped
links, no body schema). See `references/okf-spec.md` (drawn from the official spec).

Because the format is minimal, **the value you add is everything on top of it**: a
theory of what you are modeling, a typed ontology, and disciplined authoring.

## The foundation: sense and reference

Read `references/sense-and-reference.md` first — it is the theory the rest of this
skill rests on. In one paragraph:

Following Frege, every term has a **reference** (the object it picks out) and a
**sense** (the mode of presentation). "Morning star" and "evening star" co-refer to
Venus but present it differently. A **word embedding is a theory of sense**
(distributional similarity of presentation); **entity resolution in a knowledge
graph is a problem of reference** (which distinct senses designate the same object).
An OKF catalog is a **reference-engine**: stable concept IDs are rigid designators,
typed relations connect references, and entity resolution records informative
co-reference (`a = b`). The embedding/RAG layer is a separate **sense-engine** it
merely points to. The deepest modeling error is confusing the two — e.g. using
string/embedding *sense*-similarity to decide *reference*-identity ("Apple" the
company ≈ "apple" the fruit in sense, distinct in reference). Everything below
follows from keeping sense and reference in their proper places.

## When OKF is the right tool (and when it isn't)

An OKF catalog is **one layer in a knowledge architecture — the reference-engine.**
Before building, decide it is the right layer for the knowledge in hand, and let the
other layers keep their jobs. Whatever consumes the knowledge (an LLM generating an
answer, an agent doing a task) stitches it from several engines:

| Layer | Job | Relationship to OKF |
|---|---|---|
| **OKF catalog** | reference: what exists, how it connects, curated grounded prose | *this* |
| Vector / RAG index | sense: semantic retrieval over a larger corpus | OKF points to it via `resource:` |
| Deterministic engine | computation: a calculated result / verdict | OKF points to it; never states the result |
| Freshness layer | volatile facts (prices, cutoffs, news) | live-fetched, never stored in OKF |
| Per-user / session state | one user's data | a profile/state store, not OKF |

**Use OKF for its four jobs:**
- the **entity/reference backbone** — a canonical registry of what exists (stable
  IDs), so an agent/LLM never invents entities and can resolve co-reference;
- the **traversal layer** — answering "connected" questions via typed edges;
- the **grounding spine** — rich, sourced, cite-able content to generate from;
- the **matching vocabulary** — the controlled concepts other systems join on.

**Do not force OKF to do** freshness, computation, fuzzy semantic retrieval, or
per-user state — those are the other engines' jobs, and using the reference-engine
for them is a category error (see `sense-and-reference.md`). And if some knowledge is
purely high-volume unstructured text answered open-endedly, plain RAG is simpler:
**OKF earns its cost only where there is a curatable reference-structure worth
traversing** — stable entities and typed relationships. No structure to curate, no
reason to pay for a catalog.

**Two modes — know which you're in.** OKF's original design center (Google Cloud) is
*system knowledge for agents*: documenting your own data/systems (table schemas,
metric definitions, runbooks, join paths) so an agent that acts on them understands
them. A second, equally valid mode is a *domain knowledge base for generation*:
curated subject-matter an LLM retrieves from to answer end users. The format is
neutral to both, but the consumer and the stakes differ — the agent-consumer wants
precise machine-readable facts; the generator-consumer wants rich, cite-able prose
(so the rich-body discipline below matters even more there). If one product needs
both, keep them as **separate bundles** — one grounds an agent's understanding of its
own systems, the other grounds answers about the world. Do not conflate them.

## The principle that governs authoring

**OKF is a content-management format. The body is the sense; the identity and
relations are the reference — you need both.** The frontmatter (concept ID, type,
typed `relations`, `resource`) fixes reference; the markdown body carries the sense —
the mode of presentation, the descriptive content a human reads and an LLM retrieves.

A node whose body is a two-line description is a **reference with no sense**: it tells
you *that* the object exists but not *how it is given*. That is a bare pointer, not
knowledge. So the failure mode to fear most is not a wrong tag — it's a **thin body**.
When you ingest a rich source (a YAML rule set, a CSV with 30 useful columns, a
spec), render *all* of its substance into the body. This is the single most common
mistake and a core reason this skill exists.

## The workflow

Follow these steps in order. Each links to a reference for depth. Keep every step
grounded in **authoritative sources the user provides** — never invent facts, not
even "well-known" ones. Every entry carries `resource:` + `source:` proving where
its content came from. (See `references/pitfalls.md` for why.)

### 1. Scope: decide what the catalog indexes vs. points to

Having confirmed OKF is the right layer (see "When OKF is the right tool" above),
scope what *this* catalog holds. The catalog holds the **stable spine +
classification + relationships**. It does NOT hold: heavy computation,
semantic-search vectors, freshness content (prices, news, live cutoffs), or per-user
data. For those, an entry *points* via `resource:` and the value is fetched at query
time. Over-stuffing the catalog with things that belong in an engine, a vector
index, or a live feed is a design smell. The bundle is a **source format, not a
query engine** — you compile it into a serving layer later (§8).

### 2. Build the source registry (one authoritative source per folder)

For every folder/concept-type, name the single authoritative source that feeds it
(a CSV, a directory of YAMLs, an official API, a spec). Write this down — it is the
provenance contract. Then **extract each source to a reviewable intermediate file
first** (a CSV/YAML under a `*-sources/` directory) with per-row review flags for
anything the parser is unsure about. This is the **curation gate**: the user
eyeballs the extraction before any entries are generated from it. Deterministic
extraction beats hand-transcription — write a script, don't retype 500 rows.

### 3. Design the typed vocabulary (the value-add layer)

This is what lifts your bundle above vanilla OKF. Define, in one file
(`vocabulary.py`, see `scripts/`):
- **Governed types** — the allowed `type` values, each with the extra frontmatter
  fields it requires.
- **Typed predicates** — the relationship kinds you'll use (`located_in`,
  `authored_by`, `broader`/`narrower`, `depends_on`, …), each with an inverse.
  OKF leaves links untyped; you make them typed so the graph is queryable.
- **Governed tags** — a controlled list + patterns; no ad-hoc tag invention.
- **Provenance layers** — official / editorial / encyclopedic / freshness, and
  which types may draw facts from which layer.

Full patterns and rationale: `references/typed-ontology.md`.

### 4. Mirror the source's structure — do not invent a taxonomy

If the source already has an organizing structure (a directory tree, a
classification hierarchy, official categories), **mirror it**. The source's
taxonomy is authoritative; your invented grouping is not. (Hard-won: flattening a
source's own directory tree into invented "families" is a common mistake, corrected
by mirroring the real tree.) Nest folders where nesting carries meaning (products
under their category, modules under their package, cities under their region).

### 5. Write one ingester per source — with RICH bodies

One deterministic, re-runnable script per source reads the authoritative data and
emits entries + `index.md`. For each entry:
- **Frontmatter** carries the machine-queryable fields (ids, type-required fields,
  tags, typed `relations`, `resource`, `source`, `timestamp`).
- **Body** carries the *full* knowledge from the source: every substantive field,
  rendered readably (lead text, duties, requirements, criteria, tables, examples,
  classification, cross-references). If a source field is missing, leave it blank —
  never fill it from training data.
- **Structured sources hide content in comments.** `yaml.safe_load` and most
  parsers DROP comments, but the plain-language explanation is often the richest
  part. Extract comment blocks from the *raw text* and render them as prose.

Before shipping any entry type, run the **body-richness check**: open a generated
file and ask "does this contain the full useful content of the source, or did I
summarize it away?" If it's a stub, you're not done. See
`references/pitfalls.md#thin-bodies`.

### 6. Entity resolution — a problem of reference, not sense

When a field holds free-text entities (author names, product names, place names,
tags), you must resolve variants to canonical concepts. This is a **reference**
problem: which distinct senses designate the same object. **Naive string/embedding
clustering is wrong** because it measures *sense*-similarity and cannot settle
*reference*-identity ("Apple" the company ≈ "apple" the fruit in sense, distinct in
reference). So: deterministic normalization for trivial sense-variants (case,
whitespace, plural fold) + a curated, auditable canonical map (a YAML the user owns —
reference judgments a human makes) + a **review-candidates file** for the long tail.
**Right-size granularity to the query need** — not so granular you get hundreds of
singletons, not so coarse that "which services use PostgreSQL" dissolves into a
"databases" bucket. Log what you drop; never truncate silently. When in doubt, keep
entities distinct — a false `a = b` corrupts the graph more than a missed one. Full
playbook: `references/entity-resolution.md`.

### 7. Validate — and guard it in CI

Run `scripts/validate_catalog.py <bundle>` (it reads your `vocabulary.py`). It
checks: every non-reserved file has parseable frontmatter with a governed `type`;
required fields present per type; `resource` present for regulated types; every
`relations` predicate is governed; every relation target resolves to a real entry;
every tag is governed. Add a root `index.md` (carrying the governed vocabulary so
it's agent-browsable inside the bundle) and a `log.md`. Wire the validator into a
test so the bundle can't silently rot.

### 8. Consume the catalog (the serving side)

The bundle is the source of truth; consuming it is a **file-backed lookup, not a RAG
system**. The frontmatter indexes and typed relations ARE the retrieval structure —
you don't embed anything. `scripts/okf_lookup.py` is the reusable reader:

- **search** — deterministic BM25 over field-weighted frontmatter + body (title and
  aliases above body), with stopword stripping and an exact-match tier. IDF makes
  natural-language queries weigh the discriminative terms, not the common ones.
- **load** — return an entry's full Markdown body (resolving folder-as-concept ids).
- **traverse** — walk the relations graph in ONE direction (`incoming=True` gives the
  inverse without writing reverse edges to disk).
- **neighbors** / graph-aware `format_entries` — attach a concept's outbound relations
  so a *relational* question is answered from the graph, not the model's memory.

Three pitfalls the serving side must respect (see `references/consuming-okf.md`):
1. **Search alone can't answer relational questions.** The related entities (e.g. the
   pathways an occupation qualifies for) usually don't lexically match the query —
   they're reachable only via the graph. Attach neighbours; don't make the model chase
   them (it will hallucinate instead).
2. **Don't truncate away the relational section.** Rich bodies carry their
   relations/classification at the END; a naive char cap removes exactly the answer.
3. **Traversal is directional.** `located_in` outbound is "where X is"; inbound is
   "what is in X". Conflating them floods the result — match the stored label, pick the
   direction explicitly.

If you also derive a relational/vector serving layer, keep the bundle as the source of
truth and regenerate — don't hand-edit downstream.

## Self-check before you call it done

Read `references/pitfalls.md` and confirm you avoided each. The big ones:
1. **Thin bodies** — the body carries the source's full substance, not a stub.
2. **Invented content** — every fact traces to a `resource:`/`source:`; nothing
   from training data.
3. **Invented taxonomy** — the structure mirrors the source, not your imagination.
4. **Untyped/ungoverned graph** — types, predicates, tags are governed + validated.
5. **Bad entity resolution** — deterministic + curated + reviewable + right-sized.
6. **Silent truncation** — anything dropped is logged.
7. **Catalog as everything-store** — computation/search/freshness/per-user are
   *pointed to*, not stored.
8. **Consumption that hallucinates past the graph** — search-only + truncated bodies
   miss relational answers; traverse the graph and don't cut the relational section.

## Bundled scripts (reuse, don't reinvent)

In `scripts/` — copy these into the project's tooling directory and adapt:
- **`okf_io.py`** — `slugify`, `fm` (frontmatter renderer that drops empty fields
  and quotes safely), `write`, `unique_stem` (collision-free slugs). The shared IO
  every ingester uses so on-disk format is produced one way.
- **`vocabulary.py`** — the typed-ontology template: `TYPES`, `PREDICATES`,
  `RESOURCE_REQUIRED`, `tag_allowed`, optional `dynamic_tags`. Customize the
  contents for the domain; keep the shape.
- **`validate_catalog.py`** — the parameterized validator. Reads a bundle dir + a
  `vocabulary.py`; enforces everything in §7. Project-agnostic.
- **`okf_lookup.py`** — the consumption/serving reader (step 8):
  `Catalog.from_bundle(dir)` + `load_catalog` (cached), `search` (BM25 + exact-match
  tier + `exclude_types`), `load`, `traverse` (directional, `incoming=`), `neighbors`,
  and graph-aware `format_entries`. Bind the bundle path in a project `get_catalog()`
  + thin `search_okf`/`load_okf` wrappers. Project-agnostic.

Write per-source ingesters (`build_<source>.py`) in the project using `okf_io` +
`vocabulary`; those are domain-specific and stay in the project, not the skill.

## Sources

- **Format:** the official OKF spec, `GoogleCloudPlatform/knowledge-catalog` (v0.1) —
  summarized in `references/okf-spec.md`. This is the only external source of truth.
- **Method + philosophy:** original to this skill (`references/sense-and-reference.md`,
  `typed-ontology.md`, `entity-resolution.md`, `pitfalls.md`, `consuming-okf.md`),
  distilled from real OKF builds. Not derived from any third-party OKF toolkit.
