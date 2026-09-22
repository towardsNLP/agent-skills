# The philosophical foundation: sense and reference

This is the theory the whole skill rests on. It is not decoration — it explains
*why* the methodology is what it is, and it is the fastest way to avoid the deepest
modeling errors. Read it before you build.

## Frege's distinction

Gottlob Frege, *Über Sinn und Bedeutung* (1892): a term has both a **reference**
(*Bedeutung*) — the object it picks out — and a **sense** (*Sinn*) — the mode of
presentation, the way that object is given to us.

His example: "the morning star" and "the evening star" have the **same reference**
(the planet Venus) but **different senses** (Venus-as-seen-at-dawn vs.
Venus-as-seen-at-dusk). The senses differ, and that difference carries real
information. This is why the identity statement

> the morning star = the evening star

is *informative*, while "the morning star = the morning star" is trivial. `a = a`
tells you nothing; `a = b` is a discovery — the discovery that two different modes
of presentation designate one and the same object.

**That discovery is exactly entity resolution.** When we assert that "Mark Twain"
and "Samuel Clemens" name one author, or that "NYC", "New York City", and "New
York, NY" designate one place, or that "H₂O" and "water" pick out one compound, we
are making an informative `a = b`. A knowledge graph is, in large part, a structured
record of such co-reference discoveries.

## The two sentences that anchor this skill

- **A word embedding is a theory of sense.** It is a *distributional* theory of
  sense (Firth, 1957: "you shall know a word by the company it keeps") — it captures
  modes of presentation and contextual similarity. Vector search / RAG retrieves by
  sense: what is *presented similarly*.
- **Entity resolution in a knowledge graph is a problem of reference.** It asks
  which distinct senses designate the *same object*, and it fixes identity. The
  concept ID is a rigid designator (Kripke, *Naming and Necessity*) that holds the
  same reference across contexts; typed relations connect references; ER establishes
  co-reference.

A knowledge system therefore has two faculties, and they are categorically distinct:

| Faculty | What it does | Where it lives |
|---|---|---|
| **Sense-engine** | similarity of presentation; fuzzy retrieval | embeddings / vector index / RAG |
| **Reference-engine** | identity, co-reference, typed relations | the OKF catalog (this skill) |

## The two category errors (the deep bugs)

**Error 1 — solving a reference problem with a sense tool.** Using string or
embedding similarity to decide identity. "Apple" the company and "apple" the fruit
are *close in sense* (identical string, nearby embeddings) but *distinct in
reference*; so are "Java" the language and "Java" the island, or "Georgia" the
country and "Georgia" the US state. Sense proximity cannot settle reference identity
— so naive clustering mis-merges, structurally, every time. This is why correct entity
resolution needs reference-level judgment and a human curation gate: the fact of
co-reference is not recoverable from sense alone. (This is the exact bug behind
every over-eager merge; see `entity-resolution.md`.)

**Error 2 — demanding sense-work from a reference system.** Expecting the catalog
to do fuzzy semantic retrieval. It is not built for that and should not try. The
catalog *points to* the vector index via `resource:`; it does not contain it. Keep
the faculties in separate, cooperating layers.

## How Fregean roles map onto OKF constructs

| OKF construct | Fregean role |
|---|---|
| concept ID (file path / slug) | **rigid designator** — fixes reference across contexts |
| `resource:` | reference anchor — where the real object lives |
| `type` + required fields | the kind of object referred to |
| typed `relations:` | structure *between references* (the graph's real content) |
| entity resolution / canonical map | establishing informative `a = b` (co-reference) |
| `aliases`, `tags` | multiple **senses** collected under one reference |
| the rich **body** | the **sense** — the mode(s) of presentation of the referent |
| the vector index it points to | the distributional **sense-engine**, a separate layer |

## What this tells you to do

1. **The catalog is a reference system — invest in identity.** Stable, source-derived
   concept IDs (rigid designators); explicit typed relations between references;
   deliberate entity resolution. Identity is the backbone; get it right first.

2. **Never decide reference by sense-similarity.** Entity resolution is curated and
   auditable, not clustered. Deterministic normalization handles trivial sense
   variants (plurals, casing); everything else is a *reference judgment* a human
   makes in the canonical map. When in doubt, keep entities distinct — a false
   `a = b` corrupts the graph more than a missed one.

3. **Keep sense and reference in their own layers.** The catalog fixes identity and
   relations; the embedding index does similarity. They cooperate through `resource:`
   pointers. Do not collapse them — that collapse is the most common architectural
   mistake in "just throw it in a vector DB" knowledge systems.

4. **Give every reference its sense — write rich bodies.** A concept ID with a
   two-line body is a reference with no mode of presentation: it tells you *that*
   the object exists but not *how it is given*. That is not knowledge, it is a bare
   pointer. Conversely, a pile of embeddings with no identity is sense with no
   reference — ungrounded similarity. Knowledge needs both: a fixed reference,
   richly presented.

5. **Insight is reference-structure, not sense-proximity.** "Insight = traversal,
   not hairball" means the value is in following typed edges between *identified*
   entities — the informative `a = b` and the relations among references — not in
   what merely sits nearby in embedding space. Traversal is reasoning over reference;
   similarity is retrieval over sense. Build for both, but never confuse them.
