# Installing the skills in a project

Each repo declares the marketplace and the plugin in its own committed
`.claude/settings.json`. Whoever sets up the project adds those keys and the profile once; after
that, a contributor clones the repo, trusts the folder, and the skills are available, with no
install command to run.

## 1. Add this to the repo's `.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "towardsnlp-agent-skills": {
      "source": { "source": "github", "repo": "towardsNLP/agent-skills" }
    }
  },
  "enabledPlugins": { "sdd@towardsnlp-agent-skills": true }
}
```

If the file already exists, merge these two keys into it rather than replacing the file.

The repository is public, so no credentials are needed. A private fork resolves through each
contributor's existing GitHub credentials, so anyone who has already run `gh auth login` needs no
extra setup.

## 2. Add the project's profile

Copy `../templates/profile.md` to `planning/agent/profile.md` in the repo and fill it in.
Every skill reads its project-specific values from that one file. Commit it.

## 3. Remove the old committed copies

Once the plugin loads, delete the repo's own `.claude/skills/` copies of these skills.
Leaving both in place means two versions of the same workflow disagree silently.

Skills from a plugin are namespaced, so they are invoked as `/sdd:start-session`, not
`/start-session`. That namespace is also why they cannot collide with a personal skill of
the same name.

## Personal skills, in any host

`./bin/link.sh` links the `thinking/`, `knowledge/` and `craft/` skills into `~/.claude/skills`
and `~/.agents/skills`. Editing a skill here then updates every install at once; re-run it after
adding, removing or renaming one. The `sdd/` and `session/` skills are not linked, for the reason
in *Precedence* below, so outside Claude Code they have no install path yet.

Hosts differ in where they look and how a skill is called:

| Host | Reads | Call a skill with |
|---|---|---|
| Claude Code | `~/.claude/skills`, and the plugin | `/name`, or `/sdd:name` for the plugin's skills |
| Codex | `~/.agents/skills` | `$name` |
| GitHub Copilot | `~/.copilot/skills` and `~/.agents/skills` | `/name` |
| Cursor | `~/.claude/skills` and `~/.agents/skills` | `/name`; with both folders linked, a skill may be listed twice |

### Why symlinks into `~` rather than a shared folder

Claude Code walks *up* the directory tree looking for `.claude/skills`, but **stops at the git
repo root**. Measured with a probe skill, not assumed: placed in a parent folder, it was ABSENT
from a session started inside a nested git repo and FOUND from a sibling folder that was not a
repo. Projects are almost always repos, so a `.claude/skills` in a parent folder is invisible from
inside all of them. User scope is the only location that works everywhere.

## Two install scopes, and the trap between them

The directory grouping still says what each skill is *for*, but **as of 0.6.0 it no longer decides
what installs where: the plugin declares all 23.** The two scopes remain, and they install
completely differently.

| Scope | What | How it installs | Who gets it |
|---|---|---|---|
| **Project** | **all 23 skills — every one `plugin.json` declares** | as a plugin, declared in a repo's `.claude/settings.json` | everyone who clones that repo |
| **Personal** | everything in `thinking/` `knowledge/` `craft/` | `bin/link.sh` symlinks them into `~/.claude/skills` and `~/.agents/skills` | whoever runs it, in every project |

**Why 0.6.0 stopped drawing the line at 13.** 0.5.0 added four cross-scope skills because the
workflow refuses to proceed without them: `adr-spec` will not write a spec's scope without a
grilling and sends the user to `/grill-me`; `deconstruct` will not author a glossary term and hands
the gap to `domain-modeling`; `implement` says to use `/tdd`; and `tdd` sends the reader to
`codebase-design` for the module and seam vocabulary. Declaring only the nine shipped a workflow
that **stopped at its first real step** for anyone without the personal set.
`tests/test_plugin_manifest.py` refuses a manifest whose skills depend on a skill it does not ship
— the fourth of the four was found by that test, not by reading.

That reasoning has no natural stopping point at 13. A **team** without the personal set is in the
same position as a contributor without it, one step further along: the workflow runs, and then
someone needs `research`, `writing-for-agents` or `handoff` and does not have it. Shipping the
remaining nine (and `fusion`, since 0.8.0) means a collaborator installs **one plugin and nothing
else** — no clone of this
repo, no `bin/link.sh`, no personal scope at all.

Being in both costs nothing: `bin/link.sh` makes symlinks, so a personal copy and the plugin copy
are the same bytes, and the plugin's namespacing (`/sdd:tdd`) keeps the two invocations distinct.
**It costs context, though** — 23 descriptions load in every session of every repo that enables the
plugin, not 13. `skillOverrides: "name-only"` is the lever, per-skill and per-repo; see *Trimming
context cost* below.

## Precedence, and the trap it sets

Claude Code resolves same-named skills in this order:

    enterprise > personal (~/.claude/skills/) > project (.claude/skills/) > bundled

A personal skill **silently shadows** a project skill with the same name. If you keep a
personal copy of `start-session` while a repo still commits its own, you run your version
and your teammates run theirs, with no warning and no error. Never hold the same skill
name in two scopes. Plugin namespacing avoids the problem entirely, which is the main
reason these ship as a plugin rather than as personal skills, and why `bin/link.sh` links only
the three personal-scope directories.

## Trimming context cost

Invocation intent is recorded for both hosts. Claude Code reads `disable-model-invocation` from
`SKILL.md`. OpenAI products read `policy.allow_implicit_invocation` from
`agents/openai.yaml`. **6 of 23 are model-invoked.** The other 17 remain available by explicit
invocation.

An explicit skill may still have a metadata cost. Measured 2026-09-23 in a Claude Code session
with 32 skills loaded, the nine explicit project skills cost **~560 tokens**, and seven explicit
personal skills another **~280**. Invocation policy changes who can reach a skill. It does not
guarantee identical context accounting across hosts. Measure with the host's context inspector.

`skillOverrides` in settings controls what a skill costs when it is not being used:

```json
{
  "skillOverrides": {
    "some-skill": "name-only",
    "another-skill": "off"
  }
}
```

`name-only` keeps the skill invokable but suppresses its description. `off` hides it.

**Measured 2026-09-23, and the answer is the one that costs money:** `disable-model-invocation:
true` stops Claude invoking a skill on its own, but **the description is still loaded.** Nine
`user-only` project skills cost ~560 tokens in every session in that repo. The flag governs *who
can reach* the skill, not whether it occupies context.

`skillOverrides: name-only` is the lever that actually removes the description. Use `/skills` to
read per-skill costs directly rather than inferring them.

## Updating

Bump `version` in `.claude-plugin/plugin.json`, commit, push. Contributors pick the change
up automatically; `/plugin marketplace update towardsnlp-agent-skills` forces it immediately.
