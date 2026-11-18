---
title: Repository structure (work in progress)
parent: Progress records
nav_order: 3
---

# Repository structure: work in progress

**Last updated:** 18 November 2026<br>
**Status:** Further restructuring is proposed, not yet agreed.

## Completed

- Grouped documentation under `docs/` and added a local just-the-docs preview
  for a potential GitHub Pages site (commit `821ade2`).
- Moved the historical test harness into the
  [pre-refactor archive](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/tree/main/archive/pre-refactor-test-harness)
  and updated its QA references (commit `2e31cae`). Its README records the
  source commit and explains that the snapshot is historical evidence.

## Current categories

| Location | Role |
| --- | --- |
| `data/` | Sample sales data used by the running agent. |
| `datasets/` | Question sets used for evaluation and Phoenix uploads. |
| `versions/` | Agent version settings. |
| `requirements/` | Compliance specification and schema, not Python dependencies. |
| `results/` | Generated local results and logs, separate from tracked inputs. |
| `archive/pre-refactor-test-harness/` | Historical QA evidence, not the current tests. |
| `pyproject.toml` | Python project configuration and dependencies. |

The sample data, datasets and version files are runtime inputs, even though
tests also use them. Setup creates missing inputs; it does not overwrite
existing ones.

## Proposed follow-up

- Consider grouping `data/`, `datasets/` and `versions/` under one clearly
  named runtime-input location. No destination has been selected and no runtime
  files have been moved.
- Consider a clearer name or location for `requirements/` to distinguish the
  compliance specification from Python dependency requirements.
- Keep generated `results/` separate from tracked inputs, and keep
  `pyproject.toml` at the repository root.

## Decisions and checks before moving runtime inputs

The existing paths are used by setup, agent execution, dataset uploads and
tests. Existing workspaces can also contain user-edited inputs. Decide how to
handle those files before changing the layout:

1. Copy existing inputs to the new layout during setup without overwriting
   files; decide how to report conflicts when both locations contain data.
2. Require and document manual migration.
3. Keep reading the existing paths for compatibility while using the new
   layout for new workspaces.

No option has been chosen. Once agreed, update dependent code, tests and
documentation, and verify fresh setup, existing inputs, agent lookup, version
loading and dataset uploads. Preserve generated results and user data.
