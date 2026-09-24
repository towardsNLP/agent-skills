"""Safety checks for the personal-skill linker."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def run_linker(home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "bin/link.sh"],
        cwd=REPO,
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        check=False,
    )


def test_linker_refuses_to_replace_a_real_directory(tmp_path: Path):
    target = tmp_path / ".claude/skills/grill-me"
    target.mkdir(parents=True)
    sentinel = target / "mine.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    result = run_linker(tmp_path)

    assert result.returncode == 1
    assert "refusing to replace non-symlink" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "keep me"


def test_a_non_directory_destination_stops_the_run_before_anything_is_linked(tmp_path: Path):
    """The whole point of the pre-flight: the second destination decides the first one's fate."""
    first = tmp_path / ".claude/skills"
    first.mkdir(parents=True)
    stale = first / "grill-me"
    stale.symlink_to(tmp_path / "old-target")  # a link the run would otherwise repoint

    blocked = tmp_path / ".agents/skills"
    blocked.parent.mkdir(parents=True)
    blocked.write_text("not a directory", encoding="utf-8")

    result = run_linker(tmp_path)

    assert result.returncode == 1
    assert "is not a directory" in result.stderr
    assert str(blocked) in result.stderr
    assert list(first.iterdir()) == [stale]
    assert stale.readlink() == tmp_path / "old-target"
    assert blocked.read_text(encoding="utf-8") == "not a directory"


def test_a_dangling_symlink_destination_is_rejected(tmp_path: Path):
    """`-e` is false for a link with nothing behind it, so `-L` has to be tested too."""
    first = tmp_path / ".claude/skills"
    first.mkdir(parents=True)

    blocked = tmp_path / ".agents/skills"
    blocked.parent.mkdir(parents=True)
    blocked.symlink_to(tmp_path / "gone")

    result = run_linker(tmp_path)

    assert result.returncode == 1
    assert "is not a directory" in result.stderr
    assert list(first.iterdir()) == []


def test_a_symlinked_destination_directory_is_still_usable(tmp_path: Path):
    """Only a non-directory is refused. A link to a real directory is a normal install."""
    real = tmp_path / "synced-skills"
    real.mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/skills").symlink_to(real)

    result = run_linker(tmp_path)

    assert result.returncode == 0, result.stderr
    assert (real / "grill-me").is_symlink()
    assert (real / "grill-me").resolve() == REPO / "thinking/grill-me"
