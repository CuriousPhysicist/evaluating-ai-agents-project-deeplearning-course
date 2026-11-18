---
title: Repository structure (work in progress)
parent: Progress records
nav_order: 3
---

# Repository structure: work in progress

**Last updated:** 18 November 2026<br>
**Status:** Runtime inputs have been grouped; existing workspaces require
manual migration. Moving compliance specifications remains proposed.

## Completed

- Grouped documentation under `docs/` and added a local just-the-docs preview
  for a potential GitHub Pages site (commit `821ade2`).
- Moved the historical test harness into the
  [pre-refactor archive](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/tree/main/archive/pre-refactor-test-harness)
  and updated its QA references (commit `2e31cae`). Its README records the
  source commit and explains that the snapshot is historical evidence.
- Grouped runtime inputs under `inputs/`. Updated dependent code, tests,
  documentation and the source specification's path wording.

## Current categories

| Location | Role |
| --- | --- |
| `inputs/data/` | Sample sales data used by the running agent. |
| `inputs/datasets/` | Question sets used for evaluation and Phoenix uploads. |
| `inputs/versions/` | Agent version settings. |
| `requirements/` | Compliance specification and schema, not Python dependencies. |
| `results/` | Generated local results and logs, separate from tracked inputs. |
| `archive/pre-refactor-test-harness/` | Historical QA evidence, not the current tests. |
| `pyproject.toml` | Python project configuration and dependencies. |

The sample data, datasets and version files are runtime inputs, even though
tests also use them. Setup creates missing inputs; it does not overwrite
existing ones.

## Proposed follow-up

- Move the compliance specification and schema to a clearer location.

## Migration decision

Manual migration was chosen to preserve user-edited inputs. The tool does not
copy or delete existing inputs, and it reports legacy files rather than
silently selecting new defaults. See the
repository [migration instructions](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course#runtime-inputs-and-migration)
before using an existing workspace. Generated results remain separate and
`pyproject.toml` stays at the repository root.
