# Pre-refactor test harness snapshot

These files preserve the test harness and supporting code from commit
`77483a50e596b0dc30cdb598627fb625691db7f6`, before the QA refactoring.
They are historical evidence, not the current test suite.

The `.py.txt` files retain their original contents but are not collected as
Python tests:

- `tests/test_core.py.txt` - historical test harness
- `agent_evals/scripted.py.txt` - scripted stand-in used for context
- `agent_evals/__main__.py.txt` - historical setup definitions

The [granular QA assessment](../../docs/qa/QA_CHECK_1_granular.md) describes
how these files were inspected; the historical tests were not rerun for it.
