"""Checks that pinned provenance stays explicit and internally consistent."""

from __future__ import annotations

import hashlib
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "UPSTREAM.toml"


def load_manifest():
    return tomllib.loads(MANIFEST.read_text(encoding="utf-8"))


def test_sources_pin_full_commit_shas():
    data = load_manifest()
    for source in data["sources"]:
        commit = source["commit"]
        assert len(commit) == 40
        assert all(char in "0123456789abcdef" for char in commit)
        assert source["license"]
        assert source["last_compared"]


def test_skill_entries_resolve_and_use_known_statuses():
    data = load_manifest()
    sources = {source["id"] for source in data["sources"]}
    statuses = {"vendored", "adapted", "inspired", "reimplemented"}

    for skill in data["skills"]:
        assert skill["source"] in sources
        assert skill["status"] in statuses
        assert (ROOT / skill["local_path"] / "SKILL.md").is_file()
        assert skill["upstream_path"].endswith("/SKILL.md")
        assert skill["changes"]


def test_notice_accounts_for_every_borrowed_skill():
    """A hand-maintained attribution list is one that quietly goes wrong.

    NOTICE is what the upstream MIT licences actually require to travel with a copy,
    so an entry added to the manifest and forgotten here is a licensing defect, not a
    formatting one.
    """
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    data = load_manifest()

    missing = sorted({s["local_path"] for s in data["skills"]} - set(notice.split()))
    assert not missing, f"borrowed skills absent from NOTICE: {missing}"

    for source in data["sources"]:
        assert source["repository"] in notice, source["id"]


def test_vendored_skill_files_keep_the_pinned_content():
    for skill in load_manifest()["skills"]:
        if skill["status"] != "vendored":
            continue
        content = (ROOT / skill["local_path"] / "SKILL.md").read_bytes()
        assert hashlib.sha256(content).hexdigest() == skill["sha256"]
