---
name: check-contracts
description: Validate a proposed name, path, ID, branch, interface, dependency or output against this project's governing documents, resolved at check time from planning/agent/profile.md. Stops on a violation rather than fixing it.
disable-model-invocation: true
---

# Check contracts

Validate a proposed change against this project's own contracts.

This skill stores **no project facts**. It resolves them at check time from
`planning/agent/profile.md`, which supplies `doc_precedence_order`, `authority_map` (question to
the file or command that owns the answer), `constraints_doc`, `spec_path_pattern`,
`workstream_id_scheme`, `branch_convention`, `gated_changes`, `forbidden_terms` and `write_scope`.

## When to run it

Before introducing any name that outlives the change: a module, class, public function, route,
table or column, enum value, rule, spec or workstream ID, branch, file path, persisted artifact,
dependency, or top-level directory. For data and knowledge work this also covers dataset fields,
units, grain and identifiers; source, claim, metric, model and artifact IDs; ontology classes,
properties and IRIs; and rule-family names. Also run it before generating non-trivial code and
before drafting any external-facing artefact.

## Workflow

1. **Categorise** the change: name, path, ID, branch, interface, dependency, constraint, output,
   dataset contract, metric, source, model revision, knowledge term or ontology IRI.
2. **Resolve the owner** through `authority_map`. Where code owns the answer, read the code
   or run the command. Never a document's copy of it, and never a remembered value.
3. **Read the owning source now.** It may have changed this session.
4. **Compare** the proposal against the canonical entry.
5. **On a match**, proceed. **On no match**, stop and surface three things: the rule, the
   document or module that declares it, and two options. Either use the canonical
   alternative, which is preferred, or amend the owning source first, stating the old
   contract, the new contract, the migration impact, and whether a higher-level revision is
   required.
6. **Check `constraints_doc`.** A breach there is a hard stop, not a warning.
7. **Check `gated_changes`.** If the change touches one, name the gate and its approver,
   flag the dependency, and do not work around it.
8. **Scan the proposed code** for anything in `forbidden_terms`.
9. **Apply `doc_precedence_order`.** When two valid sources cover the same question, follow the
   declared precedence. When no precedence is declared for the collision, report drift and stop.

## Failure modes

| Failure | Recovery |
|---|---|
| Proposed name absent from the sources | Stop. Use a canonical name, or amend the source first. |
| Proposed name matches a forbidden entry | Stop. Pick a non-forbidden alternative. |
| No source section covers this category | Stop. Add the section, get approval, then proceed. |
| Generated code already carries a non-canonical name | Reject it. Do not commit. Regenerate once the name is settled. |
| Two sources disagree, doc against code or doc against doc | Stop. Report it as a drift bug, citing both. Neither side wins automatically. Do not quietly fix either one. |

## Hard rules

- **No project fact belongs in this file.** Anything an owner can answer is resolved, never
  copied. A fact found here is a bug in this skill.
- **Never fix a violation automatically, and never resolve a source-against-source mismatch
  automatically.** Surface it, cite it, stop.
- **No silent expansions.** A new ID family, layer, interface, model, enum or top-level
  directory needs the owning source updated first.
- **This skill is read-only** over the governing documents and over everything `write_scope`
  denies. It validates. It never authors.
- **Never bypass the active spec.** Its section 3 boundaries and section 5 proof are load-bearing.
  Work outside them goes back to the user.
