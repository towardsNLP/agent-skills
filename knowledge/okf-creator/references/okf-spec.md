# OKF format reference (v0.1)

The Open Knowledge Format, published by Google Cloud (June 2026, Apache 2.0,
`GoogleCloudPlatform/knowledge-catalog`). It formalizes the "LLM-wiki pattern"
into a portable, vendor-neutral convention: a directory of markdown files any tool
can read without an SDK. Deliberately minimal — the value you add sits on top.

## Frontmatter

| Field | Status | Notes |
|---|---|---|
| `type` | **REQUIRED** | The only required field. A short string identifying the concept kind. Consumers route/filter/present on it; no central registry. |
| `title` | recommended | Human display name; consumers may derive from filename if absent. |
| `description` | recommended | One-sentence summary for previews/search. |
| `resource` | recommended | URI identifying the underlying asset (omit for abstract concepts). |
| `tags` | recommended | YAML list of strings for cross-cutting categorization. |
| `timestamp` | recommended | ISO 8601 datetime of last meaningful change. |

Producers may add arbitrary extra fields. Consumers MUST preserve unknown keys when
round-tripping and SHOULD NOT reject documents with unrecognized fields.

## Reserved files

- **`index.md`** — a directory listing for progressive disclosure. No frontmatter.
  May appear in any directory including the bundle root. Put the governed
  vocabulary in the root `index.md` so it is agent-browsable inside the bundle.
- **`log.md`** — chronological change history with ISO 8601 date headings.

All other `.md` files are concept documents.

## Links

Concepts link with standard markdown, in two forms:
- **Bundle-relative (absolute):** begins with `/` — `[customers](/tables/customers.md)`
- **Relative:** standard path — `[neighbor](./other.md)`

A link asserts a relationship; **the kind of relationship is conveyed by prose, not
by the link** (OKF links are untyped). This is the format's key limitation — you
cannot query "all tables that join to customers" from vanilla OKF. The fix is the
typed-ontology layer (see `typed-ontology.md`): put machine-readable typed edges in
a frontmatter `relations:` block *in addition to* prose links.

## Conformance (§9)

A bundle conforms if:
1. Every non-reserved `.md` file has parseable YAML frontmatter.
2. Every frontmatter block has a non-empty `type`.
3. Reserved filenames follow their structures when present.

Consumers MUST NOT reject a bundle for: missing optional fields, unknown types,
unknown keys, broken links, or missing index files. OKF is intentionally tolerant.

## What OKF does NOT give you (and you must add)

- **Typed relationships** — add a governed predicate set + a `relations:` block.
- **A body schema** — add per-type body conventions so entries are consistent and
  content-rich.
- **Validation** — add a validator (bundled with this skill).
- **Entity resolution** — messy source vocabularies need it; the format won't help.

OKF's own strength for you is that it is so minimal it is *disposable*: even if the
standard changes, your bundle is just markdown + YAML you can transform with a short
script. You are really betting on your typed ontology, which is format-independent.
