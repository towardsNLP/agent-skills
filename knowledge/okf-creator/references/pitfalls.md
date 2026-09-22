# Pitfalls checklist — self-audit before shipping a bundle

These are the mistakes that make an OKF catalog useless despite looking done. Each
was paid for in real builds. Check every one.

## thin-bodies (the #1 mistake)

**Symptom:** a node's body is a 2–3 line description while the source was rich.
**Why it's fatal:** OKF is a content-management format. The body is the knowledge —
it's what the LLM retrieves and what a human reads. A stub body means the "knowledge
structure" carries no knowledge, so the whole graph is decorative.
**Fix:** render the *full* substance of the source into the body — every useful
field (descriptions, duties, requirements, criteria, tables, examples,
classification, cross-references). Run the **body-richness check** on a sample file
of each type: "does this contain the source's full useful content, or did I
summarize it away?" If it reads like a stub, you are not done.
**Special case:** structured sources (YAML/TOML/INI) hide their richest content in
*comments*, and parsers drop comments. Extract the comment blocks from raw text and
render them as prose — the plain-language rule explanation is often the best part.

## invented-content

**Symptom:** facts in an entry that aren't in any provided source ("well-known"
capitals, plausible descriptions, guessed URLs).
**Why it's fatal:** it silently corrupts the knowledge base with unverifiable
claims, and in regulated domains it's dangerous.
**Fix:** every fact traces to a `resource:`/`source:`. You build the *machinery*
(structure, ingesters, vocabulary, validator); the user provides the *content*. If a
source field is missing, leave it blank — never fill it from training data. If a
folder needs data you don't have, mark it "needs source" and stop, don't fabricate.

## invented-taxonomy

**Symptom:** you reorganized the source's structure into your own "cleaner"
grouping.
**Why it's a mistake:** the source's structure (a directory tree, an official
classification) is authoritative; your invented grouping is not, and it desyncs from
the source over time.
**Fix:** mirror the source's structure. Nest only where nesting carries real meaning.

## untyped-or-ungoverned-graph

**Symptom:** free-text tags, prose-only links, no validator.
**Fix:** governed types + typed predicates + governed tags + a validator that
enforces them and checks that every relation target resolves. See
`typed-ontology.md`.

## bad-entity-resolution

**Symptom:** either hundreds of singleton nodes, or everything crushed into a few
vague buckets; or a keyword/embedding rule that mis-merges (`Apple Inc.` under
`apple` the fruit; `Java` the language under `Java` the island).
**Why it's fatal:** it's a category error — using *sense*-similarity to decide
*reference*-identity (see `sense-and-reference.md`). Sense proximity cannot settle
whether two names pick out the same object; a false `a = b` corrupts the graph.
**Fix:** deterministic normalization for trivial sense-variants + a curated canonical
map (reference judgments a human makes) + a review-candidates file + a granularity
decision the user makes (show them the distribution). See `entity-resolution.md`.

## silent-truncation

**Symptom:** a threshold, a top-N, a dropped-because-unmatched, with no record of
what was cut.
**Why it matters:** silent truncation reads as "covered everything" when it didn't.
**Fix:** log what you drop (a `*_below_threshold.csv`, a review file, a printed
count). The raw value stays in the entity body regardless.

## catalog-as-everything-store

**Symptom:** dumping computation outputs, ML vectors, live prices, or per-user data
into markdown files.
**Why it's wrong:** those belong in an engine, a vector index, a live feed, or the
user's profile store — the catalog *points* to them via `resource:` and they're
fetched at query time. A 300-dimension embedding vector, or a full data table's
rows, dumped into every file is the tell.
**Fix:** the catalog holds the stable spine + classification + relationships only.

## hand-editing-derived-output

**Symptom:** editing the compiled serving-layer data (Postgres rows, a vector index)
directly.
**Fix:** the bundle is the source of truth; the serving layer is derived. Change the
source and regenerate — never hand-edit downstream.

## Quick final pass

1. Open one generated file of each type. Is the body rich? (thin-bodies)
2. Can you point to the source of every fact in it? (invented-content)
3. Does the folder tree match the source's structure? (invented-taxonomy)
4. Does the validator pass, with all relation targets resolving? (governance)
5. Is anything dropped without a log? (silent-truncation)
6. Is anything stored that should be pointed to? (everything-store)
