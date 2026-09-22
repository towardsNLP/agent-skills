# Agent profile

Copy this to `planning/agent/profile.md` in the project and fill it in. Every skill in the
`sdd` plugin reads its project-specific values from here, so nothing project-specific lives
in a skill.

Delete any key that does not apply rather than leaving a placeholder. A key with a
placeholder value is worse than a missing one, because a skill will act on it.

---

## Identity and people

- **project_label:** name used in diary headers, or omit for none
- **lead:** exact `git config user.name` of the person allowed to run lead-only skills
- **contributors:** one line each — name, role, active or handing off
- **contexts:** only for multi-repo or no-git workspaces, where a session is identified by
  which repo it is in rather than by who is running it

## Diaries

- **diary_dir:** e.g. `planning/diaries/`
- **diary_filename:** e.g. `<first>-diary.md`; say how name collisions are disambiguated
- **diary_header_text:** the boilerplate a new diary opens with

## Shared planning documents

- **state_path:** `planning/STATE.md` — the generated file `/start-session` reads
- **progress_log_path:**
- **progress_log_ordering:** `append` (oldest first) or `prepend` (newest first)
- **plan_path:** the master plan
- **roadmap_path:** the status board or delivery tracker
- **contracts_path:** the project's constitution, or omit
- **modeling_handbook_path:** the domain-modelling authority, or omit
- **architecture_doc_path:** or omit
- **glossary_path:** or omit
- **sync_targets:** the exact files `/sync-progress` may write
- **doc_precedence_order:** which document wins on which question

> Keep `progress_log_ordering` honest. If the log is oldest-first and long, the newest entry
> sits past a default read cutoff and the agent will silently read stale state. Newest-first
> is the safer default.

## Specs

- **spec_dir:**
- **spec_path_pattern:** e.g. `planning/specs/spec-<id>-<slug>.md`
- **spec_template_path:**
- **spec_owner:** default owner written into new spec frontmatter
- **spec_initial_status:** e.g. `Drafted`
- **spec_frontmatter_fields:** the required field list, in order
- **workstream_id_scheme:** the ID grammar, with examples
- **phase_vocabulary:** the valid phase or increment names

## Git

- **branch_convention:** the format and the allowed types or owner prefixes
- **trunk_and_pointers:** trunk, integration, release and deploy branches, and what merging
  to each one means
- **git_scope_for_backfill:** how `/start-session` and `/sync-progress` scope `git log`

## Gates and scope

- **gate_model:** what "done" requires beyond a spec's exit criterion
- **gated_changes:** changes that need a named human's approval first, and who approves
- **ownership_gates:** components a named person owns, if any
- **readonly_paths:** paths these skills must never write
- **write_scope:** anything else the skills may or may not touch
- **forbidden_terms:** banned imports, legacy paths, deprecated names, style bans
- **non_negotiable_constraints:** the hard stops, or a pointer to the document holding them
- **constraints_doc:** where those constraints actually live

> Put confidential constraints in `constraints_doc` and point at it. Do not inline them here
> if this file is shared more widely than the constraint is.

## Reading map

- **task_category_map:** task category to the documents `/start-session` should load for it.
  This is the main lever on how much context a session costs — keep each category short.
- **open_questions_source:** where unresolved questions are tracked

## Schedule and stakeholders

- **milestones_deadlines:** dated commitments the skills should flag risk against
- **external_stakeholders:** who receives output; they never run these skills
- **stakeholder_cadence:** meeting or review rhythm
- **sizing_convention:** how effort is expressed
- **unlogged_commit_alert:** threshold at which to ping a contributor

## Housekeeping

> Never put a machine-local path in this file. It is committed and every contributor reads it, so
> `~/...` or `/Users/...` is correct for exactly one person. Agent memory in particular is
> per-user: the harness knows where its own lives.

- **regeneration_commands:** commands `/sync-progress` runs, whose diffs join the sync commit
- **draft_comms_rules:** where drafts live, and whether they are committed
- **authorship_line:** required byline on new documents, or omit
- **versioned_canonical_docs:** which version of a document is authoritative, where
  superseded copies exist
- **has_sync_progress:** `true`, or `false` for a solo project where `/end-session` also does
  the shared-doc update
