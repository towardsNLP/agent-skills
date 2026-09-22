"""Validate an OKF bundle against a project's governed vocabulary.

Project-agnostic: point it at a bundle directory and a `vocabulary.py` (see the
template in this skill). Enforces the typed-ontology layer that vanilla OKF lacks:
  - every non-reserved .md has parseable frontmatter with a governed `type`
  - required common fields (title, timestamp) + per-type required fields
  - `resource` present for RESOURCE_REQUIRED types
  - every `relations` predicate is governed
  - every relation target resolves to a real entry (file, or folder w/ index.md)
  - every tag is governed (tag_allowed)

Usage:
    python validate_catalog.py <bundle_dir> [--vocab path/to/vocabulary.py]

Exit code 0 = valid, 1 = errors (prints them). Import `validate(bundle)` from a
test to CI-guard the bundle.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

import yaml

RESERVED = {"log.md"}
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _load_vocab(path: Path):
    spec = importlib.util.spec_from_file_location("okf_vocabulary", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_frontmatter(path: Path) -> dict | None:
    m = FM_RE.match(path.read_text(encoding="utf-8"))
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        return None


def _concept_ids(bundle: Path) -> set[str]:
    """All resolvable targets: file ids (path minus .md) + folders with index.md."""
    ids: set[str] = set()
    for p in bundle.rglob("*.md"):
        rel = p.relative_to(bundle)
        ids.add(str(rel.with_suffix("")))
        if p.name == "index.md":
            ids.add(str(rel.parent))
    return ids


def validate(bundle: Path, vocab) -> list[str]:
    errors: list[str] = []
    ids = _concept_ids(bundle)
    dynamic = vocab.dynamic_tags(bundle) if hasattr(vocab, "dynamic_tags") else set()

    for path in sorted(bundle.rglob("*.md")):
        rel = str(path.relative_to(bundle))
        if path.name in RESERVED or ".ipynb_checkpoints" in rel:
            continue
        fm = parse_frontmatter(path)
        if fm is None:
            if path.name == "index.md":  # plain listing indexes need no frontmatter
                continue
            errors.append(f"{rel}: missing or unparseable frontmatter")
            continue

        ctype = fm.get("type")
        if ctype not in vocab.TYPES:
            errors.append(f"{rel}: type {ctype!r} not in governed type list")
            continue
        for field in ["title", "timestamp"] + vocab.TYPES[ctype]:
            if not fm.get(field) and fm.get(field) != 0:
                errors.append(f"{rel}: missing required field {field!r} for type {ctype}")
        if ctype in getattr(vocab, "RESOURCE_REQUIRED", set()) and not fm.get("resource"):
            errors.append(f"{rel}: type {ctype} requires `resource` (official source URI)")

        for r in fm.get("relations") or []:
            pred, target = r.get("predicate"), r.get("target")
            if pred not in vocab.PREDICATES:
                errors.append(f"{rel}: predicate {pred!r} not in governed list")
            if target not in ids:
                errors.append(f"{rel}: relation target {target!r} does not resolve")

        for tag in fm.get("tags") or []:
            if not vocab.tag_allowed(str(tag), dynamic):
                errors.append(f"{rel}: tag {tag!r} not governed")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--vocab", type=Path, default=None,
                    help="path to vocabulary.py (default: <bundle>/../vocabulary.py "
                         "or ./vocabulary.py)")
    args = ap.parse_args()
    vpath = args.vocab
    if vpath is None:
        for cand in (args.bundle.parent / "vocabulary.py", Path("vocabulary.py")):
            if cand.exists():
                vpath = cand
                break
    if not vpath or not vpath.exists():
        print("error: could not find vocabulary.py; pass --vocab")
        return 2
    vocab = _load_vocab(vpath)

    errors = validate(args.bundle, vocab)
    n = sum(1 for p in args.bundle.rglob("*.md") if ".ipynb_checkpoints" not in str(p))
    if errors:
        print(f"INVALID: {len(errors)} error(s) across {n} files")
        for e in errors[:60]:
            print(" -", e)
        if len(errors) > 60:
            print(f"   ... and {len(errors) - 60} more")
        return 1
    print(f"VALID: {n} markdown files, 0 errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
