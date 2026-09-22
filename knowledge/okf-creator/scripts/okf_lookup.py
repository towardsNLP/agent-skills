"""Consume an OKF catalog at runtime — copy into a project's tooling/runtime dir
and bind the bundle path.

The serving side of an OKF bundle: a **file-backed lookup**, not a RAG system. The
knowledge already lives in linked Markdown directories with YAML frontmatter and typed
`relations:` edges — that IS the retrieval structure. This module parses the bundle
once, then answers by:
  - ``search``   — deterministic **BM25** over field-weighted frontmatter + body,
                   with stopword stripping and an exact-match tier
  - ``load``     — fetch one entry's full Markdown body (resolves file AND folder ids)
  - ``traverse`` — walk the typed relations graph in one direction (in/out)
  - ``neighbors``— a concept's outbound relations grouped by predicate

No embeddings, no network, no LLM, no database. Project-agnostic: the only binding is
the bundle directory you pass to ``load_catalog``. Wrap it in the project with a
fixed-path ``get_catalog()`` + thin ``search_okf``/``load_okf`` functions if you like.

Why BM25 + tiering (not naive keyword scoring): IDF weights the discriminative terms
so natural-language queries aren't dominated by common words, and length normalization
stops long entries from swamping short ones. The exact-match tier floats an
entity-name query to the top; BM25 ranks within a tier.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_RESERVED = {"log.md"}
_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Function words + generic question fillers stripped from queries and the index so
# BM25's IDF weighs the discriminative terms, not NL scaffolding.
_STOPWORDS = frozenset(
    """
    a an the of for in on to and or but with as at by from that this these those it its
    i my me we our us you your he she they them their about into can could would should
    is are am was were be been being do does did has have had will
    what which who whom how why when where whose
    tell please need want get find looking help know more some any
    """.split()
)

# BM25F-style field weights (applied as term-frequency multipliers at index time).
# Aliases rank with titles (they are alternative names); body is included at low
# weight for recall but never dominates the frontmatter.
_FIELD_WEIGHTS = {"title": 3, "aliases": 3, "tags": 2, "type": 1, "body": 1}
_K1 = 1.5
_B = 0.75


def _content_tokens(text: str) -> list[str]:
    """Lowercase alphanumeric tokens with stopwords + single chars removed."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in _STOPWORDS]


@dataclass(frozen=True)
class OkfEntry:
    """One catalog entry: parsed frontmatter + the Markdown body verbatim."""

    concept_id: str          # bundle-relative path minus .md
    type: str | None
    title: str | None
    tags: tuple[str, ...]
    resource: str | None
    source: str | None
    relations: tuple[tuple[str, str], ...]   # (predicate, target) as written on disk
    frontmatter: dict
    body: str
    path: Path

    @property
    def aliases(self) -> list[str]:
        return list(self.frontmatter.get("aliases") or [])

    @property
    def provenance(self) -> str:
        """One-line source/resource attribution for the trust model."""
        parts = [p for p in (self.source, self.resource) if p]
        return " · ".join(str(p) for p in parts)

    def to_markdown(self) -> str:
        """The body prefixed with a provenance line — the payload a consumer uses."""
        prov = self.provenance
        header = f"> Source: {prov}\n\n" if prov else ""
        return f"{header}{self.body}".strip()

    def _weighted_tf(self) -> dict[str, int]:
        """Weighted term frequencies across fields (BM25F approximation)."""
        tf: dict[str, int] = {}
        fields = [
            (self.title or "", _FIELD_WEIGHTS["title"]),
            (" ".join(self.aliases), _FIELD_WEIGHTS["aliases"]),
            (" ".join(self.tags), _FIELD_WEIGHTS["tags"]),
            (self.type or "", _FIELD_WEIGHTS["type"]),
            (self.body, _FIELD_WEIGHTS["body"]),
        ]
        for text, weight in fields:
            for token in _content_tokens(text):
                tf[token] = tf.get(token, 0) + weight
        return tf


class Catalog:
    """In-memory indexes + relations graph + BM25 index over an OKF bundle."""

    def __init__(self, entries: list[OkfEntry], folder_index: dict[str, OkfEntry]):
        self._by_id: dict[str, OkfEntry] = {e.concept_id: e for e in entries}
        self._folder_index = folder_index  # folder path -> its index.md entry (folder-as-concept)

        self._by_type: dict[str, list[OkfEntry]] = {}
        self._by_tag: dict[str, list[OkfEntry]] = {}
        for e in entries:
            if e.type:
                self._by_type.setdefault(e.type, []).append(e)
            for tag in e.tags:
                self._by_tag.setdefault(tag, []).append(e)

        # Relations graph, keyed by canonical (file) concept ids in BOTH directions.
        # Files store one direction only; the inverse index lets you answer e.g.
        # "which entries point at this one?" without writing reverse edges to disk.
        self._out_edges: dict[str, list[tuple[str, str]]] = {}
        self._in_edges: dict[str, list[tuple[str, str]]] = {}
        for e in entries:
            for pred, target in e.relations:
                tcanon = self._canon(target)
                self._out_edges.setdefault(e.concept_id, []).append((pred, tcanon))
                self._in_edges.setdefault(tcanon, []).append((pred, e.concept_id))

        # BM25 index: inverted postings (term -> [(concept_id, weighted_tf)]) + lengths.
        self._postings: dict[str, list[tuple[str, int]]] = {}
        self._doc_len: dict[str, int] = {}
        for e in entries:
            tf = e._weighted_tf()
            self._doc_len[e.concept_id] = sum(tf.values())
            for term, freq in tf.items():
                self._postings.setdefault(term, []).append((e.concept_id, freq))
        n_docs = len(entries) or 1
        self._avgdl = (sum(self._doc_len.values()) / n_docs) or 1.0
        self._idf = {
            term: math.log(1 + (n_docs - len(postings) + 0.5) / (len(postings) + 0.5))
            for term, postings in self._postings.items()
        }

    # -- construction ----------------------------------------------------------
    @classmethod
    def from_bundle(cls, bundle_dir: Path) -> "Catalog":
        """Parse every *.md entry under bundle_dir and build the indexes."""
        bundle = Path(bundle_dir)
        entries: list[OkfEntry] = []
        folder_index: dict[str, OkfEntry] = {}
        for path in sorted(bundle.rglob("*.md")):
            if path.name in _RESERVED or ".ipynb_checkpoints" in str(path):
                continue
            entry = _parse(path, bundle)
            if entry is None:
                continue
            entries.append(entry)
            if path.name == "index.md":
                folder = str(path.relative_to(bundle).parent)
                folder_index[folder if folder != "." else ""] = entry
        return cls(entries, folder_index)

    # -- id resolution ---------------------------------------------------------
    def _canon(self, concept_id: str) -> str:
        """Map a folder-as-concept id to its index.md file id; leave file ids as-is."""
        entry = self._folder_index.get(concept_id)
        return entry.concept_id if entry else concept_id

    def load(self, concept_id: str) -> OkfEntry | None:
        return self._by_id.get(concept_id) or self._folder_index.get(concept_id)

    # -- search ----------------------------------------------------------------
    def search(
        self,
        query: str,
        *,
        type: str | None = None,
        tag: str | None = None,
        exclude_types: set[str] | None = None,
        limit: int = 10,
    ) -> list[OkfEntry]:
        q_raw = query.strip().lower()
        q_tokens = _content_tokens(q_raw)
        if not q_tokens:
            return []

        bm25 = self._bm25(q_tokens)
        if not bm25:
            return []

        ranked: list[tuple[int, float, str, OkfEntry]] = []
        for cid, score in bm25.items():
            e = self._by_id[cid]
            if type and e.type != type:
                continue
            if exclude_types and e.type in exclude_types:
                continue
            if tag and tag not in e.tags:
                continue
            ranked.append((self._tier(e, q_raw), score, cid, e))

        # Exact-match tier first, then BM25, then id for a deterministic tiebreak.
        ranked.sort(key=lambda r: (-r[0], -r[1], r[2]))
        return [e for _, _, _, e in ranked[:limit]]

    def _bm25(self, q_tokens: list[str]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for term in set(q_tokens):
            postings = self._postings.get(term)
            if not postings:
                continue
            idf = self._idf[term]
            for cid, freq in postings:
                dl = self._doc_len[cid]
                denom = freq + _K1 * (1 - _B + _B * dl / self._avgdl)
                scores[cid] = scores.get(cid, 0.0) + idf * (freq * (_K1 + 1)) / denom
        return scores

    @staticmethod
    def _tier(entry: OkfEntry, q_raw: str) -> int:
        """3 = query equals title/alias, 2 = query is a substring of one, 0 = BM25 only."""
        title = str(entry.title or "").lower()
        aliases = [a.lower() for a in entry.aliases]
        if q_raw == title or q_raw in aliases:
            return 3
        if q_raw and (q_raw in title or any(q_raw in a for a in aliases)):
            return 2
        return 0

    # -- traversal -------------------------------------------------------------
    def traverse(
        self,
        concept_id: str,
        predicate: str | None = None,
        depth: int = 1,
        incoming: bool = False,
    ) -> list[OkfEntry]:
        """Walk the relations graph in ONE direction.

        Outbound (default): the entities this concept points to. Inbound
        (``incoming=True``): the entities that point *at* it — the inverse edge,
        without any reverse edges being written to disk. ``predicate`` always matches
        the stored (forward) edge label, so directional queries stay unambiguous:
        outbound ``parent`` gives a node's parent; inbound ``parent`` gives its
        children.
        """
        start = self.load(concept_id)
        if start is None:
            return []
        edges = self._in_edges if incoming else self._out_edges
        seen = {start.concept_id}
        frontier = [start.concept_id]
        out: list[OkfEntry] = []
        for _ in range(max(1, depth)):
            nxt: list[str] = []
            for cid in frontier:
                for pred, other in edges.get(cid, ()):
                    if predicate is not None and pred != predicate:
                        continue
                    entry = self.load(other)
                    key = entry.concept_id if entry else other
                    if key in seen:
                        continue
                    seen.add(key)
                    if entry is not None:
                        out.append(entry)
                        nxt.append(entry.concept_id)
            frontier = nxt
            if not frontier:
                break
        return out

    def neighbors(self, concept_id: str) -> dict[str, list[OkfEntry]]:
        """Outbound relations grouped by predicate, resolved to entries.

        A concept's own typed assertions — the graph neighborhood a consumer can
        surface so a relational question is answered from the graph, not from a
        model's memory (the targets often don't lexically match the query)."""
        entry = self.load(concept_id)
        grouped: dict[str, list[OkfEntry]] = {}
        if entry is None:
            return grouped
        for pred, target in self._out_edges.get(entry.concept_id, ()):
            tgt = self.load(target)
            if tgt is not None:
                grouped.setdefault(pred, []).append(tgt)
        return grouped


def _parse(path: Path, bundle: Path) -> OkfEntry | None:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return None  # plain index.md listing or non-entry file — not a concept
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None

    concept_id = str(path.relative_to(bundle).with_suffix(""))
    relations = tuple(
        (r["predicate"], r["target"])
        for r in (fm.get("relations") or [])
        if isinstance(r, dict) and r.get("predicate") and r.get("target")
    )
    return OkfEntry(
        concept_id=concept_id,
        type=fm.get("type"),
        title=fm.get("title"),
        tags=tuple(str(t) for t in (fm.get("tags") or [])),
        resource=fm.get("resource"),
        source=fm.get("source"),
        relations=relations,
        frontmatter=fm,
        body=text[m.end():].strip(),
        path=path,
    )


@lru_cache(maxsize=8)
def load_catalog(bundle_dir: Path) -> Catalog:
    """Parse a bundle once and cache the built Catalog (keyed by path)."""
    return Catalog.from_bundle(bundle_dir)


def format_entries(
    entries: list[OkfEntry],
    *,
    catalog: Catalog | None = None,
    with_relations: bool = False,
    max_body_chars: int | None = None,
) -> str:
    """Render entries as a Markdown block for a consumer (e.g. an LLM tool result).

    Pass ``catalog`` + ``with_relations=True`` to append each entry's outbound graph
    neighbours (predicate → target titles/ids), so relational answers are grounded
    even when the targets don't lexically match the query. Avoid ``max_body_chars``
    when the answer may live at the end of a body (relations/classification sections).
    """
    blocks: list[str] = []
    for e in entries:
        body = e.body
        if max_body_chars and len(body) > max_body_chars:
            body = body[:max_body_chars].rstrip() + " …"
        prov = f"> Source: {e.provenance}\n\n" if e.provenance else ""
        block = f"### {e.title or e.concept_id}  ·  `{e.concept_id}`\n{prov}{body}"
        if with_relations and catalog is not None:
            grouped = catalog.neighbors(e.concept_id)
            if grouped:
                rel_lines = ["", "**Related:**"]
                for pred, targets in grouped.items():
                    names = ", ".join(f"{t.title} (`{t.concept_id}`)" for t in targets)
                    rel_lines.append(f"- {pred}: {names}")
                block += "\n" + "\n".join(rel_lines)
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)
