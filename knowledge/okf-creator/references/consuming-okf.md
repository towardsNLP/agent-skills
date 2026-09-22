# Consuming an OKF catalog — the serving side

Building a good catalog is half the job; the other half is *reading* it well at
runtime. OKF's payoff — grounding with provenance, and relational answers plain search
can't give — is realized (or thrown away) here. This is the method and the pitfalls,
each paid for in a real build. The reusable reader is `scripts/okf_lookup.py`.

## The method: file lookup, not RAG

The knowledge already lives in linked Markdown with typed frontmatter and `relations:`
edges. That IS the retrieval structure — you don't embed anything. Three primitives:

- **search** — find the anchor entry from free text.
- **load** — fetch an entry's full body (the payload a consumer uses).
- **traverse / neighbors** — walk the typed graph for what search can't reach.

Grounding = search finds the anchor, the graph supplies the connected knowledge, both
carry `source:`/`resource:` provenance. Embeddings are *sense* (similarity); the OKF
graph is *reference* (identity + typed relations). Consumption leans on reference.

## Why BM25 (not naive keyword scoring)

**Symptom:** a keyword scorer ranks by raw token overlap, so common words ("work",
"canada", "immigration") count as much as the discriminative ones ("underwriter",
"quispamsis"). Natural-language queries — which arrive full of common words — rank
badly.
**Fix:** BM25. Its **IDF** term weights rare/discriminative terms above common ones;
**TF-saturation + length normalization** stop a long body from swamping a short one.
Build the document from **field-weighted** frontmatter (title and aliases above body —
aliases are alternative names and carry real recall) plus the body at low weight for
fallback recall. Add an **exact-match tier** so an entity-name query floats its entry
to #1, with BM25 ranking within the tier. Strip stopwords on both sides. All
deterministic — no model, no network.

## search-only-misses-relations (the hallucination trap)

**Symptom:** the user asks a *relational* question ("what pathways can this occupation
qualify for?"). Search returns the occupation — but never the pathways, because the
pathway entries don't contain the occupation's name. The model, handed only the
occupation, fills the gap from training data and states pathways the catalog never
asserted.
**Why it's fatal:** this is the exact failure OKF exists to prevent. The correct answer
was *in the catalog* — as `qualifies_for` edges on the occupation — and the consumer
walked right past it.
**Fix:** attach the anchor's graph neighbours to the result. `neighbors()` /
`format_entries(..., with_relations=True)` appends the outbound relations (predicate →
target title + id), so the model sees the real pathways inline and can't drift. Don't
rely on the model to issue a follow-up traversal call — it won't reliably; give it the
neighbourhood up front.

## truncation-cuts-the-answer

**Symptom:** you cap body length to control context size. Answers go missing.
**Why it's fatal:** rich bodies put their **relations / classification / cross-links at
the END** (lead + description + duties + requirements come first). A char cap removes
exactly the relational section you needed. Observed live: an occupation body of ~3,000
chars with its "Immigration pathways" list starting at char ~2,550 — a 1,200-char cap
deleted the whole answer.
**Fix:** don't truncate the body. If context size bites, return **fewer entries**
(lower `limit`), not shorter ones. The graph-aware Related footer is compact
(titles+ids) and gives the relational payload without dumping more full bodies.

## traversal-is-directional

**Symptom:** you traverse `located_in` from a city expecting its province and get 50+
results (every institution, org, and site *in* the city). One predicate, two meanings,
merged.
**Why it happens:** files store an edge in one direction (`X located_in Toronto`). If
traversal follows both directions under the same label, "where is Toronto?" (outbound)
and "what's in Toronto?" (inbound) collapse together.
**Fix:** make traversal **directional**. Match the stored (forward) label and choose
the direction explicitly: outbound `located_in` = "where X is"; inbound `located_in`
(`incoming=True`) = "what is in X". Build the inverse index in memory so the inbound
query works without writing reverse edges to disk.

## structural-type-noise

**Symptom:** results are cluttered with structural entries — a `NocGroup`/unit-group
twin that near-duplicates the occupation, or `Workplace` nodes — pushing out the
substantive answers.
**Fix:** let the consumer pass `exclude_types` to drop structural types from *results*.
They stay reachable as compact graph *edges* in the Related footer, so you get dedup in
the payload without losing traversal reach.

## Self-check (serving side)

1. Does a relational question return the related **entities** (via the graph), or only
   the lexical match?
2. Is the answer ever in a part of the body you truncated away?
3. Is traversal directional, or does one predicate return both directions?
4. Do results carry provenance (`source:`/`resource:`) into the consumer?
5. Is the bundle still the source of truth — is any derived serving layer regenerated,
   not hand-edited?
