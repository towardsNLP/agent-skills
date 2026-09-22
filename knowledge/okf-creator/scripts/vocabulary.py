"""Governed vocabulary for an OKF catalog — the typed-ontology layer that lifts a
bundle above vanilla OKF. TEMPLATE: replace the domain contents with your own;
keep the shape. This one file is the single source of truth shared by every
ingester (which emits it) and the validator (which enforces it).

Read references/typed-ontology.md for the rationale behind each section.
"""

from __future__ import annotations

import re

CATALOG_VERSION = "0.1"

# --- 1. Governed concept types -> the EXTRA frontmatter each requires ----------
# A `type` not listed here is rejected by the validator. Keep the required list to
# the fields that genuinely identify/qualify the concept.
TYPES: dict[str, list[str]] = {
    # examples span domains — replace with your own:
    # "Dataset":  ["schema", "owner"],       # data catalog
    # "Author":   [],                         # bibliographic
    # "Compound": ["formula", "cas_number"],  # chemistry
    # "Service":  ["language", "repo"],       # software map
    "Concept": [],   # replace with your domain types
}

# Types whose facts are regulated/official -> a `resource:` (official source URI)
# is REQUIRED. This is how unsourced facts are kept out of regulated entries.
RESOURCE_REQUIRED: set[str] = set()   # e.g. {"Dataset", "Compound"}

# --- 2. Typed relation predicates (the queryable edges) ------------------------
# OKF links are untyped; you make them typed here. Include inverses so the graph
# reads both ways. Keep the set small and reusable.
PREDICATES: set[str] = {
    "broader", "narrower",            # hierarchy (SKOS-style)
    "in_category", "has_member",      # classification
    "located_in", "contains",         # place
    "related_to",                     # generic fallback
    # add domain edges (examples): "authored_by"/"authored",
    # "depends_on"/"required_by", "cites"/"cited_by", "joins_to", ...
}

# --- 3. Governed tags ----------------------------------------------------------
# A controlled base list + generative patterns + slugs the catalog derives from
# its own structure (passed in as `dynamic`). No ad-hoc tag invention.
BASE_TAGS: set[str] = {
    # "occupation", "category", "city", "pathway", ...
}
TAG_PATTERNS: list[re.Pattern] = [
    # re.compile(r"^level-[0-5]$"),
    # re.compile(r"^year-\d{4}$"),
]


def tag_allowed(tag: str, dynamic: set[str]) -> bool:
    return tag in BASE_TAGS or tag in dynamic or any(p.match(tag) for p in TAG_PATTERNS)


def dynamic_tags(bundle) -> set[str]:
    """Optional: slugs the catalog derives from its own structure (e.g. category
    folder names, place slugs) that are legal as tags. Return a set; the validator
    passes it to tag_allowed. Default: none.

    `bundle` is a pathlib.Path to the bundle root.
    """
    return set()
