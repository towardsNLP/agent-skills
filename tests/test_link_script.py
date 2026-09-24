"""Safety checks for the personal-skill linker."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_linker_refuses_to_replace_a_real_directory(tmp_path: Path):
    target = tmp_path / ".claude/skills/grill-me"
    target.mkdir(parents=True)
    sentinel = target / "mine.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    env = {**os.environ, "HOME": str(tmp_path)}
    result = subprocess.run(
        ["bash", "bin/link.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "refusing to replace non-symlink" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "keep me"
