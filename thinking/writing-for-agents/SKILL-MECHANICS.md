# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, the invocation choice, and router skills). Everything else about writing it is the universal reference in `SKILL.md`.

## Invocation

Two choices, trading the two loads:

- A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation always _includes_ user reach; a description only ever adds agent discovery, never removes the human's. The description is the skill's top-level context pointer, forced to stay loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is also one home for shared reference: another skill can invoke it, so reference needed by several skills lives in one place. Mechanics: omit `disable-model-invocation`, and write a model-facing description carrying the trigger branches (the pointer-writing rules in `SKILL.md` apply in full).
- A **user-invoked** skill prevents autonomous invocation: the human must type its name, and other
  skills cannot depend on the model discovering it. This reduces discoverability but does not
  guarantee zero context load. Some harnesses still load its name and description. Measure with
  the harness's context inspector; use `name-only` or `off` overrides where supported. Mechanics:
  set `disable-model-invocation: true`; the `description` becomes human-facing, with trigger lists
  stripped.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must.
If it only ever fires by hand, make it user-invoked and measure the remaining metadata cost in the
target harness.

Shared reference that two user-invoked skills both need can live in neither: with no descriptions, neither can fire the other. Push it to a plain file outside the skill system: external reference any skill can point at.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): split off a model-invoked skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.

## Router skills

When user-invoked skills multiply past what you can remember, that piled-up cognitive load is cured
by a **router skill**: one user-invoked skill that names the others and when to reach for each, so
the human has one skill to remember instead of many. It recommends the next user-invoked skill;
the human invokes it.
