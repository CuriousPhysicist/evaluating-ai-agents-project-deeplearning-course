---
title: CLI and Module Refactoring Strategy
nav_order: 2
parent: Design
---

# CLI and Module Refactoring Strategy

**Last Updated:** November 22, 2026

## Overview

This document outlines anticipated refactoring patterns for CLI routing and module organization as the codebase grows. It captures design decisions made during code review to avoid premature optimization while remaining prepared for future architectural evolution.

## Current Architecture

### CLI Routing (`agent_evals/__main__.py`)

**Current Pattern:**
- Top-level imports for CLI parser setup (argparse, json, paths)
- Conditional imports within command handlers (lazy-loading of command-specific dependencies)
- Single-file dispatch router (171 lines)

**Rationale:**
- Reduces startup time for quick commands
- Avoids loading heavy dependencies unnecessarily
- Idiomatic Python CLI pattern (Django, Flask, Click all use this)
- Keeps imports co-located with their usage

**Reference Commits/Reviews:**
- Code review conversation: Exit codes refactoring and module structure analysis (Nov 22, 2026)

---

## Refactoring Triggers

### ✅ No Refactoring Needed If:
- `__main__.py` remains < 300 lines
- No shared command logic emerges across handlers
- Each command handler fits cleanly in the conditional branch
- Import statements remain readable and organized
- Tests remain fast and independent

### ⚠️ Refactoring Recommended If:
- **File exceeds 300+ lines** → Extract command handlers
- **Shared logic patterns emerge** → Extract to `agent_evals/cli/_common.py` or similar
- **Command handlers exceed 50 lines each** → Extract to dedicated command modules
- **Circular dependency appears** → Indicates module boundary issues
- **New contributor struggles to understand dispatch flow** → Sign it's time to refactor

---

## Recommended Refactoring Strategies

### Stage 1: Extract Handler Functions (Minimal Impact)

**When:** `__main__.py` reaches 250+ lines OR command logic becomes complex

**Changes:**
```python
# Before
elif args.command == "ask":
    from .agent import run_agent
    from .recording import ensure_phoenix
    # ... 20 lines of logic

# After
def _handle_ask(args):
    from .agent import run_agent
    from .recording import ensure_phoenix
    # ... 20 lines of logic

# In main():
handlers = {
    "setup": _handle_setup,
    "ask": _handle_ask,
    "evaluate": _handle_evaluate,
    # ...
}
handlers[args.command](args)
```

**Pros:**
- Cleaner dispatch logic
- Easier to test individual commands
- Imports still conditional
- No new files needed

**File Location:** Keep in `__main__.py`

---

### Stage 2: Extract Command Modules (Significant Growth)

**When:** One or more handler functions exceed 50 lines OR multiple commands share utilities

**Structure:**
```
agent_evals/cli/
├── __init__.py
├── __main__.py              # Router only
├── _commands/
│   ├── __init__.py
│   ├── setup.py             # setup() command
│   ├── ask.py               # ask command
│   ├── evaluate.py          # evaluate command
│   ├── compare.py           # compare command
│   ├── assurance.py         # assurance commands
│   └── _common.py           # Shared utilities
```

**Implementation:**

```python
# agent_evals/cli/__main__.py
def main():
    args = parser.parse_args()
    
    # Route to handlers (imports on-demand)
    if args.command == "setup":
        from ._commands.setup import handle_setup
        handle_setup(args)
    elif args.command == "ask":
        from ._commands.ask import handle_ask
        handle_ask(args)
    # ... etc
```

**Pros:**
- Each command is self-contained
- Easier to add new commands without touching router
- Clear ownership (dev can find ask logic quickly)
- Imports still conditional (performance preserved)
- Shared utilities in `_common.py` reduce duplication

**Cons:**
- More files to navigate initially
- Requires careful `__init__.py` management to avoid circular imports

---

### Stage 3: Consolidate Configuration and Core Classes

**When:** `compliance_check.py` exceeds 700 lines OR extensibility requirements emerge

**Current Status:** Monitored but not yet implemented

See: [Compliance Check Module Analysis](../progress/COMPLIANCE_CHECK_STRUCTURE.md) (if created)

**Current Plan:** Keep `ThresholdConfig`, `RegressionDetector`, `ComplianceChecker` in single file until clear extensibility driver emerges.

---

## Module Organization Principles

### 1. **Separation of Concerns**
- CLI routing → Command dispatch and argument parsing
- Configuration → Threshold loading and validation
- Logic → Compliance checking, regression detection
- Data → Results, tracking, serialization

### 2. **Dependency Flow**
```
cli/__main__.py (router)
    ↓
cli/compliance_check.py (config + logic)
    ↓
cli/commands/*.py (command handlers) [if extracted]
    ↓
exit_codes.py (contracts)
```

### 3. **Import Strategy**
- **Top-level:** Minimal dependencies (only CLI framework)
- **Conditional:** Command-specific logic (lazy-loaded)
- **Never circular:** Imports flow outward only

---

## Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-11-22 | Keep `__main__.py` as single-file router | Current scale (171 lines) is manageable; no complexity yet | ✅ Approved |
| 2026-11-22 | Conditional imports are appropriate | Standard pattern for CLI routers; enables lazy-loading | ✅ Approved |
| 2026-11-22 | Keep `compliance_check.py` classes together | Tightly coupled; tested together; no extensibility need yet | ✅ Approved |
| 2026-11-22 | Document refactoring strategy proactively | Avoid architectural surprises as codebase grows | ✅ Approved |

---

## Monitoring Checklist

Use this checklist during code reviews to decide if refactoring is needed:

- [ ] Is `__main__.py` approaching 300 lines?
- [ ] Are there multiple handlers > 50 lines each?
- [ ] Are command-related utilities being duplicated?
- [ ] Is compliance checking logic exceeding 700 lines?
- [ ] Are there circular import warnings?
- [ ] Do new contributors ask "where does X logic live?"
- [ ] Are tests becoming slow or interdependent?

If **2+ checkboxes** are marked, review this document and trigger refactoring.

---

## References

- [Phase 1 Scoring Architecture](Phase_1_Scoring_Architecture.md)
- [Repository Structure](../repository-structure.md)
- Python standard practices: [The Twelve-Factor App - Processes](https://12factor.net/processes)
- Click Framework: [Command Groups and Chaining](https://click.palletsprojects.com/en/8.1.x/commands/)
