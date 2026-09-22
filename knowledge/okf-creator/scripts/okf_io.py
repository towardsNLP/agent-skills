"""Shared OKF authoring helpers — copy into a project's tooling dir; every
ingester uses these so the on-disk format is produced exactly one way.

Project-agnostic. No domain assumptions.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def slugify(text: str) -> str:
    """Stable, ASCII, url-safe slug. Source-derived slugs keep concept ids stable
    across regenerations, so make the slug from stable source fields."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-"))


def fm(fields: dict) -> str:
    """Render an ordered dict as YAML frontmatter.

    - Empty values are DROPPED (a missing source field stays absent, never
      invented or written as empty).
    - `relations` renders as a list of {predicate, target} maps.
    - Scalars containing YAML-significant chars are quoted safely; URLs are left
      bare.
    """
    lines = ["---"]
    for k, v in fields.items():
        if v in (None, ""):
            continue
        if k == "relations":
            lines.append("relations:")
            for r in v:
                lines.append(f"  - {{predicate: {r['predicate']}, target: {r['target']}}}")
        elif isinstance(v, list):
            lines.append(f"{k}: [{', '.join(map(str, v))}]")
        else:
            s = str(v).replace("\n", " ").strip()
            if s.startswith("http"):
                lines.append(f"{k}: {s}")
            elif any(c in s for c in ":#'\","):
                lines.append(f'{k}: "{s.replace(chr(34), chr(39))}"')
            else:
                lines.append(f"{k}: {s}")
    return "\n".join(lines + ["---"])


def write(path: Path, fields: dict, body: str) -> None:
    """Write one concept file: frontmatter + a blank line + the (rich) body."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fm(fields) + "\n\n" + body.strip() + "\n", encoding="utf-8")


def unique_stem(seen: set[str], base: str) -> str:
    """Deterministic collision-free slug within a folder (two entities that slug
    to the same base get -2, -3, …)."""
    if base not in seen:
        seen.add(base)
        return base
    i = 2
    while f"{base}-{i}" in seen:
        i += 1
    seen.add(f"{base}-{i}")
    return f"{base}-{i}"


def yaml_comment_block(raw: str, stop_at_first_key: bool = True) -> list[str]:
    """Extract the leading plain-language comment block from a structured file's
    RAW text. Parsers (yaml.safe_load, etc.) drop comments, but the comment block
    is often the richest human explanation of a rule/asset — render it into the
    body. Skips divider lines and `key: ...` section-label comments.

    Returns the comment lines (without the leading '# ').
    """
    out: list[str] = []
    for line in raw.splitlines():
        st = line.strip()
        if st.startswith("#"):
            c = st.lstrip("#").strip()
            if c and set(c) <= set("-—= "):        # divider line
                continue
            if re.match(r"^[a-z_]+:\s", c):          # section-label comment
                continue
            out.append(c)
        # break only at a BLOCK-start key (`key:` with nothing after) — inline
        # header scalars (`stream: Study Permit`) are skipped so the comment block
        # that follows them is still collected.
        elif stop_at_first_key and re.match(r"^[a-zA-Z_]+:\s*$", line):
            break
    return out
