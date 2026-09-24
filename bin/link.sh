#!/usr/bin/env bash
set -euo pipefail

# Link every personal-scope skill into the harness skill directories:
#   ~/.claude/skills  -> Claude Code
#   ~/.agents/skills  -> Codex and other Agent Skills-compatible harnesses
#
# Each entry is a symlink back here, so editing a skill updates every install at
# once. Re-run after adding, removing or renaming a skill.
#
# Only PERSONAL_DIRS are linked. The remaining directories are project-scope: they
# ship as a plugin and are installed per-repo, so that collaborators get them too.
# Linking a project-scope skill here would shadow the repo's own copy silently --
# personal scope wins over project scope, with no warning. See docs/install.md.
#
# Why symlinks into ~ rather than a skills directory inside a synced folder: Claude
# Code walks UP the directory tree looking for .claude/skills, but STOPS AT THE GIT
# REPO ROOT. Every real project is its own repo, so a .claude/skills placed in a
# parent folder is invisible from inside them. Measured, not assumed.
#
# Pattern adapted from Matt Pocock's scripts/link-skills.sh (mattpocock/skills, MIT).

PERSONAL_DIRS=(thinking knowledge craft)

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")

for DEST in "${DESTS[@]}"; do
  if [ -L "$DEST" ]; then
    resolved="$(readlink "$DEST")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $DEST is a symlink into this repo ($resolved)." >&2
        echo "Remove it and re-run; the script will recreate it as a real directory." >&2
        exit 1
        ;;
    esac
  fi
  mkdir -p "$DEST"
  for dir in "${PERSONAL_DIRS[@]}"; do
    for src in "$REPO/$dir"/*/; do
      src="${src%/}"
      name="$(basename "$src")"
      target="$DEST/$name"
      if [ -e "$target" ] && [ ! -L "$target" ]; then
        echo "error: refusing to replace non-symlink $target" >&2
        echo "Move it aside or remove it yourself, then re-run." >&2
        exit 1
      fi
      ln -sfn "$src" "$target"
      echo "linked $name -> $DEST"
    done
  done
done
