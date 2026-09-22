# Installing the skills in a project

Each repo declares the marketplace and the plugin in its own committed
`.claude/settings.json`. A contributor clones the repo, trusts the folder once, and the
skills are available. There is no install command to run and nothing to copy.

## 1. Add this to the repo's `.claude/settings.json`

```json
{
  "extraKnownMarketplaces": {
    "agent-skills": {
      "source": { "source": "github", "repo": "towardsNLP/agent-skills" }
    }
  },
  "enabledPlugins": { "sdd@agent-skills": true }
}
```

If the file already exists, merge these two keys into it rather than replacing the file.

Private-repo access resolves through each contributor's existing GitHub credentials, so
anyone who has already run `gh auth login` needs no extra setup.

## 2. Add the project's profile

Copy `../templates/profile.md` to `planning/agent/profile.md` in the repo and fill it in.
Every skill reads its project-specific values from that one file. Commit it.

## 3. Remove the old committed copies

Once the plugin loads, delete the repo's own `.claude/skills/` copies of these skills.
Leaving both in place means two versions of the same workflow disagree silently.

Skills from a plugin are namespaced, so they are invoked as `/sdd:start-session`, not
`/start-session`. That namespace is also why they cannot collide with a personal skill of
the same name.

## Precedence, and the trap it sets

Claude Code resolves same-named skills in this order:

    enterprise > personal (~/.claude/skills/) > project (.claude/skills/) > bundled

A personal skill **silently shadows** a project skill with the same name. If you keep a
personal copy of `start-session` while a repo still commits its own, you run your version
and your teammates run theirs, with no warning and no error. Never hold the same skill
name in two scopes. Plugin namespacing avoids the problem entirely, which is the main
reason these ship as a plugin rather than as personal skills.

## Trimming context cost

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

Note: the published docs state that `disable-model-invocation: true` stops Claude from
invoking a skill on its own, but they do not say whether the description still occupies
context. `skillOverrides: name-only` is the documented lever for that. Measure with
`/context` before and after rather than assuming.

## Updating

Bump `version` in `.claude-plugin/plugin.json`, commit, push. Contributors pick the change
up automatically; `/plugin marketplace update agent-skills` forces it immediately.
