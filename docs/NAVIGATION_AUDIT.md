---
title: "Documentation Navigation Audit & Improvements"
nav_order: 7
---

# Documentation Navigation Audit & Improvements

**Date:** 19 November 2026  
**Purpose:** Review Jekyll site navigation structure for completeness and identify improvement opportunities  
**Scope:** All 35 documentation files across 5 sections  
**Status:** ✅ Audit complete - 8 improvements identified

---

## Executive Summary

The documentation site is **well-structured** with:
- ✅ All 35 files have proper Jekyll frontmatter
- ✅ Hierarchical parent-child relationships working
- ✅ 5 main sections properly organized
- ✅ Consistent navigation metadata

**However, 8 improvements are recommended** to enhance discoverability and cross-referencing:

1. ⚠️ Some QA and Design files lack visible navigation links
2. ⚠️ Phase 1a & 1b index pages are sparse (missing file listings)
3. ⚠️ Repository structure docs not linked from main index
4. ⚠️ Missing cross-section reference guide
5. ⚠️ Some parent pages need descriptions/purpose
6. ⚠️ Missing "where to find" guide for different roles
7. ⚠️ BRANCH_MERGE_STATUS not referenced from main navigation
8. ⚠️ Top-level index missing Jekyll site disclaimer

---

## Current Navigation Structure

```
📚 docs/ (Root)
  nav_order: Home (1)
  
├─ 📄 index.md (Main entry)
│  └─ Sections table with 4 links
│
├─ 1️⃣ spec/ (nav_order: 2)
│  └─ index.md (has_children: true)
│     ├─ evaluating-ai-agents-spec-62ab422.md (nav_order: 1)
│     ├─ resolved-decisions.md (nav_order: 2)
│     └─ spec_test_suite_proposal.md (nav_order: 3)
│
├─ 2️⃣ qa/ (nav_order: 3)
│  └─ index.md (has_children: true)
│     ├─ QA_CHECK_1.md (nav_order: 1)
│     ├─ QA_CHECK_1_granular.md (no nav_order)
│     ├─ QA_CHECK_2.md (nav_order: 2)
│     ├─ qa_refactor_plan.md (nav_order: 6)
│     ├─ score_comparison_1.md (no nav_order)
│     └─ score_comparison_2.md (no nav_order)
│
├─ 3️⃣ design/ (nav_order: 4)
│  └─ index.md (has_children: true)
│     └─ Phase_1_Scoring_Architecture.md (nav_order: 1)
│
└─ 4️⃣ progress/ (nav_order: 5)
   └─ index.md (has_children: true)
      ├─ PHASE_1_COMPLETION_RECORD.md (nav_order: 4)
      ├─ OUTSTANDING_TASKS_AND_GAPS.md (nav_order: 10)
      ├─ PHASE_1c_QUICK_REFERENCE.md (nav_order: 8)
      ├─ PHASE_1c_DEPENDENCY_DIAGRAM.md (nav_order: 11)
      ├─ BRANCH_MERGE_STATUS.md (nav_order: 12) ⚠️ Not in index
      ├─ repository-structure.md (nav_order: 3)
      │
      ├─ 🔹 phase-1a/ (nav_order: 1)
      │  └─ index.md (has_children: true)
      │     ├─ PHASE_1_INDEX.md (no nav_order)
      │     ├─ PHASE_1_IMPLEMENTATION.md (no nav_order)
      │     ├─ QUICK_REFERENCE.md (no nav_order)
      │     ├─ PHASE_1_CHECKLIST.md (no nav_order)
      │     ├─ PHASE_1_COMPLETION_SUMMARY.md (no nav_order)
      │     └─ FINAL_SUMMARY.md (no nav_order)
      │
      └─ 🔹 phase-1b/ (nav_order: 2)
         └─ index.md (has_children: true)
            ├─ PHASE_1b_INDEX.md (no nav_order)
            ├─ PHASE_1b_PLAN.md (no nav_order)
            ├─ PHASE_1b_PYTEST_INTEGRATION.md (no nav_order)
            ├─ PHASE_1b_CI_CD_SETUP.md (no nav_order)
            ├─ PHASE_1b_COMPLETION_SUMMARY.md (no nav_order)
            └─ PYTEST_PLUGIN_LOADING_RESOLUTION.md (no nav_order)
```

---

## Issues Identified

### 🔴 Issue #1: QA Section Missing File Descriptions

**Location:** `docs/qa/index.md`  
**Problem:** Index page is minimal; doesn't list the 7 QA files with descriptions  
**Impact:** Users can't see what QA documents exist without navigating sidebar

**Current state:**
```markdown
---
title: QA reviews
has_children: true
nav_order: 3
---

# QA reviews

Spec-vs-harness checks, score comparisons and the QA refactor plan.
```

**Recommendation:** Add descriptive table of QA files

---

### 🔴 Issue #2: QA Files Missing nav_order

**Location:** `docs/qa/`  
**Files affected:**
- QA_CHECK_1_granular.md
- score_comparison_1.md
- score_comparison_2.md

**Problem:** 3 of 7 QA files lack `nav_order` in frontmatter  
**Impact:** Ordering unpredictable; Jekyll sorts alphabetically, but shouldn't rely on this

**Solution:** Add nav_order to these files:
- QA_CHECK_1_granular.md → nav_order: 3 (after QA_CHECK_1_granular)
- score_comparison_1.md → nav_order: 4
- score_comparison_2.md → nav_order: 5

---

### 🟡 Issue #3: Design Section Only Has One Document

**Location:** `docs/design/index.md`  
**Problem:** Design section appears empty except for one file  
**Impact:** Looks incomplete; users wonder if there's more design documentation

**Current state:** Only `Phase_1_Scoring_Architecture.md` exists (should reference `Phase_1a/PHASE_1_IMPLEMENTATION.md` as architecture reference)

**Solution:** Update index.md to clarify that Phase_1a's implementation docs also contain design decisions

---

### 🟡 Issue #4: Phase-1a & Phase-1b Index Pages are Sparse

**Location:** `docs/progress/phase-1a/index.md` and `docs/progress/phase-1b/index.md`  
**Problem:** Only have title and brief description; don't list their child documents  
**Impact:** New readers don't know what documentation exists in each phase

**Current Phase 1a:**
```markdown
---
title: Phase 1a
has_children: true
nav_order: 1
parent: Progress records
---

# Phase 1a

Generic compliance scoring engine.
```

**Solution:** Add descriptive tables listing all files with their purposes

---

### 🟡 Issue #5: BRANCH_MERGE_STATUS Not Referenced from Progress Index

**Location:** `docs/progress/index.md`  
**Problem:** BRANCH_MERGE_STATUS.md exists but isn't mentioned in the navigation guide  
**Impact:** Users might not find the branch cleanup documentation

**Solution:** Add entry in "Documentation Map" section explaining its purpose and when to use it

---

### 🔵 Issue #6: Main Index Missing Site Disclaimer

**Location:** `docs/index.md`  
**Problem:** Doesn't clarify this is Jekyll-generated documentation  
**Impact:** Users might not understand how to build/deploy the site

**Solution:** Add note at the bottom about Jekyll generation and GitHub Pages

---

### 🔵 Issue #7: No Cross-Reference Guide

**Problem:** No document explains how different sections relate to each other  
**Impact:** Difficult for new readers to understand overall structure

**Solution:** Create a "Documentation Map" at root level explaining relationships

---

### 🔵 Issue #8: Missing "Role-Based" Quick Links

**Problem:** Current quick-starts only in progress/index.md  
**Impact:** Other sections don't help users find content by role

**Solution:** Add quick-start guides to other section indices

---

## Recommended Improvements

### **Priority 1: Quick Fixes (< 1 hour)**

#### 1.1 Add nav_order to QA Files

Add to frontmatter of these files:

**docs/qa/QA_CHECK_1_granular.md**
```yaml
---
title: "QA check 1 (granular)"
parent: QA reviews
nav_order: 3
---
```

**docs/qa/score_comparison_1.md**
```yaml
---
title: "Score comparison 1"
parent: QA reviews
nav_order: 4
---
```

**docs/qa/score_comparison_2.md**
```yaml
---
title: "Score comparison 2"
parent: QA reviews
nav_order: 5
---
```

---

#### 1.2 Enhance QA Index Page

Update `docs/qa/index.md` to include file descriptions:

```markdown
---
title: QA reviews
has_children: true
nav_order: 3
---

# QA reviews

Spec-vs-harness checks, score comparisons and the QA refactor plan.

## 📚 Quality Assurance Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [QA Check 1](QA_CHECK_1.md) | Spec requirements vs test harness coverage | Reviewers |
| [QA Check 1 (Granular)](QA_CHECK_1_granular.md) | Detailed coverage assessment per requirement | Developers |
| [QA Check 2](QA_CHECK_2.md) | Test suite quality assessment | Leads |
| [Score Comparison 1](score_comparison_1.md) | Before/after scoring analysis | Stakeholders |
| [Score Comparison 2](score_comparison_2.md) | Detailed score comparison report | Analyzers |
| [QA Refactor Plan](qa_refactor_plan.md) | Refactoring strategy and progress | Project leads |

**Use these when:**
- Validating specification coverage
- Reviewing test quality
- Tracking score improvements
- Understanding evidence confidence
```

---

#### 1.3 Add BRANCH_MERGE_STATUS to Progress Index

In `docs/progress/index.md`, add to the Documentation Map:

```markdown
#### 6. **BRANCH_MERGE_STATUS.md** (10.3 KB) ⚠️ Archive
**Type:** Branch verification and cleanup record
**Key Sections:**
- Branch verification summary
- Squash merge explanation
- Deletion instructions and execution record
- Safety analysis

**When to Use:**
- **Historical Reference:** Understanding why branches were deleted
- **Learning:** How squash merges work and when to delete branches
- **Team Communication:** Explaining branch cleanup decisions

**Link:** [Read BRANCH_MERGE_STATUS.md](BRANCH_MERGE_STATUS.md)

**Note:** This is a historical record. Both branches (refactor_test_suite and feat_develop_metric) were squashed into main (commits fa8e2a3 and 31b4b66) and subsequently deleted on 18 Nov 2026.
```

---

### **Priority 2: Structure Enhancements (1-2 hours)**

#### 2.1 Enhance Phase-1a Index

Update `docs/progress/phase-1a/index.md`:

```markdown
---
title: Phase 1a
has_children: true
nav_order: 1
parent: Progress records
---

# Phase 1a: Generic Compliance Scoring Engine

Automated calculation of compliance scores based on evidence from test results.

## 📚 Phase 1a Documentation

| Document | Purpose |
|----------|---------|
| [Phase 1 Index](PHASE_1_INDEX.md) | Navigation guide for Phase 1a deliverables |
| [Implementation Guide](PHASE_1_IMPLEMENTATION.md) | Technical implementation details and design decisions |
| [Quick Reference](QUICK_REFERENCE.md) | One-page summary of key features |
| [Checklist](PHASE_1_CHECKLIST.md) | Verification checklist for Phase 1a completion |
| [Completion Summary](PHASE_1_COMPLETION_SUMMARY.md) | Summary of achieved outcomes |
| [Final Summary](FINAL_SUMMARY.md) | Executive summary and key metrics |

## 🎯 Key Deliverables

**Generic Scoring Engine**
- Five-level evidence rubric (insufficient → exceeds)
- Configurable requirement specifications (YAML)
- Weighted score calculation
- 100% test coverage (87.34%)

**Configuration-Driven Design**
- Not hardcoded for T1-T21
- Reusable with any specification
- Supports custom evidence levels

**Test Integration**
- 30 new tests in Phase 1a
- 155 total tests passing (100% pass rate)
- Zero regressions

See [Architecture](../../design/Phase_1_Scoring_Architecture.md) for design decisions.
```

---

#### 2.2 Enhance Phase-1b Index

Update `docs/progress/phase-1b/index.md`:

```markdown
---
title: Phase 1b
has_children: true
nav_order: 2
parent: Progress records
---

# Phase 1b: Pytest Integration and CI/CD Automation

Automated evaluation pipeline with pytest integration and CI/CD compliance gates.

## 📚 Phase 1b Documentation

| Document | Purpose |
|----------|---------|
| [Phase 1b Index](PHASE_1b_INDEX.md) | Navigation guide for Phase 1b deliverables |
| [Plan & Design](PHASE_1b_PLAN.md) | Planning and design decisions |
| [Pytest Integration](PHASE_1b_PYTEST_INTEGRATION.md) | How to use the pytest plugin |
| [CI/CD Setup](PHASE_1b_CI_CD_SETUP.md) | Integration examples and configuration |
| [Completion Summary](PHASE_1b_COMPLETION_SUMMARY.md) | Summary of achieved outcomes |
| [Plugin Resolution](PYTEST_PLUGIN_LOADING_RESOLUTION.md) | Troubleshooting pytest plugin issues |

## 🎯 Key Deliverables

**Pytest Plugin**
- Automatic test discovery and T-ID mapping
- Compliance reporters (JSON, HTML, console)
- 92 existing tests marked with T-IDs

**CI/CD Integration**
- Exit codes for automation
- Multi-platform examples (GitHub Actions, GitLab CI, Jenkins)
- Automated compliance reporting

**Test Suite**
- 15+ integration tests added
- 100% pass rate
- Zero regressions

See [Quick Start](../PHASE_1c_QUICK_REFERENCE.md) for getting started with Phase 1c.
```

---

#### 2.3 Enhance Design Index

Update `docs/design/index.md`:

```markdown
---
title: Design
has_children: true
nav_order: 4
---

# Design

Design decisions for the compliance scoring engine and system architecture.

## 📚 Design Documentation

| Document | Purpose | Scope |
|----------|---------|-------|
| [Phase 1 Scoring Architecture](Phase_1_Scoring_Architecture.md) | Architectural decisions for scoring engine | Phase 1 |
| [Phase 1a Implementation](../progress/phase-1a/PHASE_1_IMPLEMENTATION.md) | Technical design and implementation details | Phase 1a |
| [Phase 1b Plan](../progress/phase-1b/PHASE_1b_PLAN.md) | Pytest integration and CI/CD design | Phase 1b |

## 🎯 Key Design Principles

**Generic Framework**
- Not T1-T21-specific
- Configuration-driven (YAML specifications)
- Reusable with other specifications

**Automated Evaluation**
- Pytest integration for test discovery
- Automated reporter generation
- CI/CD-ready exit codes

**Evidence-Based Scoring**
- Five-level rubric system
- Configurable weights
- Phoenix integration for historical tracking
```

---

#### 2.4 Add Top-Level Quick Reference Guide

Create `docs/SITE_GUIDE.md`:

```markdown
---
title: "Site Navigation Guide"
nav_order: 6
---

# Agent Evals Documentation Site Guide

**Welcome!** This guide helps you navigate the documentation based on your role.

## 🎯 Quick Navigation by Role

### I want to understand what was built (Project Leads)
1. Start: [docs/ Home](index.md) - overview
2. Read: [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - summary
3. Dive deeper: [Phase 1a Docs](progress/phase-1a/index.md) & [Phase 1b Docs](progress/phase-1b/index.md)
**Time:** 20-30 minutes

### I want to review the code (Code Reviewers)
1. Start: [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - verification checklists
2. Read: [Phase 1a Implementation](progress/phase-1a/PHASE_1_IMPLEMENTATION.md)
3. Review: [QA Checks](qa/index.md) for coverage analysis
**Time:** 30-45 minutes

### I'm planning Phase 1c work (Planners)
1. Start: [Phase 1c Quick Reference](progress/PHASE_1c_QUICK_REFERENCE.md) - overview
2. Read: [Outstanding Tasks & Gaps](progress/OUTSTANDING_TASKS_AND_GAPS.md) - details
3. Plan: [Dependency Diagram](progress/PHASE_1c_DEPENDENCY_DIAGRAM.md) - sequencing
**Time:** 30-40 minutes

### I want to understand the requirements (Developers)
1. Start: [Specification](spec/index.md) - the requirements
2. Read: [QA Checks](qa/index.md) - coverage analysis
3. Reference: [Design Decisions](design/index.md) - why we built it this way
**Time:** 1-2 hours

### I want to use the tool in CI/CD (DevOps)
1. Start: [Phase 1b CI/CD Setup](progress/phase-1b/PHASE_1b_CI_CD_SETUP.md) - examples
2. Read: [Pytest Integration](progress/phase-1b/PHASE_1b_PYTEST_INTEGRATION.md) - how it works
3. Reference: [Phase 1b Plan](progress/phase-1b/PHASE_1b_PLAN.md) - design decisions
**Time:** 30 minutes

### I want architecture details (Architects)
1. Start: [Design](design/index.md) - high level
2. Read: [Scoring Architecture](design/Phase_1_Scoring_Architecture.md) - decisions
3. Deep dive: [Phase 1a Implementation](progress/phase-1a/PHASE_1_IMPLEMENTATION.md) - details
**Time:** 1 hour

## 📚 Documentation Sections

| Section | Contains | Start Here |
|---------|----------|-----------|
| [Specification](spec/index.md) | Requirements, decisions, test design | For understanding "what" |
| [QA Reviews](qa/index.md) | Coverage analysis, score comparisons | For validation |
| [Design](design/index.md) | Architecture decisions | For understanding "why" |
| [Progress](progress/index.md) | Implementation and planning records | For "current status" |

## 🗂️ File Organization

- **docs/spec/** - Original requirements and test suite design
- **docs/qa/** - Quality assurance checks and evidence analysis
- **docs/design/** - Architectural decisions
- **docs/progress/** - Implementation progress
  - **phase-1a/** - Scoring engine implementation
  - **phase-1b/** - Pytest integration implementation
  - **OUTSTANDING_TASKS_AND_GAPS.md** - What's next (Phase 1c & beyond)
  - **PHASE_1c_DEPENDENCY_DIAGRAM.md** - Task sequencing and dependencies

## 📱 On Mobile?

Jekyll's Just-the-docs theme works on mobile. Use the ☰ menu at top-left to navigate.

## 🔍 Search

Use Ctrl+F (Windows) or Cmd+F (Mac) to search within this site.

---

**Next:** Choose your role above and jump to the right starting point! →
```

---

#### 2.5 Add Jekyll Site Note to Main Index

Update `docs/index.md` footer:

```markdown
---

## 📖 About This Site

This is a **Jekyll-generated documentation site** built from Markdown files using the [Just-the-docs](https://just-the-docs.github.io/just-the-docs/) theme.

### Building Locally

```bash
# Install Ruby dependencies
bundle install

# Build and serve
bundle exec jekyll serve
```

The site will be available at `http://localhost:4000`

### Deployment

This site is configured for automatic deployment to GitHub Pages when changes are pushed to `main`.

---

**New to this documentation?** [Start with the Navigation Guide](SITE_GUIDE.md)
```

---

### **Priority 3: Organizational Improvements (Optional)**

#### 3.1 Create a "Links Dashboard"

Add a new page at `docs/LINKS.md` to centralize all cross-references:

```markdown
---
title: "Quick Links"
nav_order: 8
---

# Quick Links

**Specification & Requirements**
- [Full Specification](spec/evaluating-ai-agents-spec-62ab422.md)
- [Resolved Decisions](spec/resolved-decisions.md)
- [T1-T21 Test Design](spec/spec_test_suite_proposal.md)

**Quality Assurance**
- [Coverage Analysis (QA Check 1)](qa/QA_CHECK_1.md)
- [Detailed Coverage (Granular)](qa/QA_CHECK_1_granular.md)
- [Quality Assessment (QA Check 2)](qa/QA_CHECK_2.md)
- [Score Comparison](qa/score_comparison_1.md)
- [Refactor Plan](qa/qa_refactor_plan.md)

**Implementation & Progress**
- [Phase 1a: Scoring Engine](progress/phase-1a/index.md)
- [Phase 1b: Pytest Integration](progress/phase-1b/index.md)
- [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md)
- [Outstanding Tasks](progress/OUTSTANDING_TASKS_AND_GAPS.md)
- [Phase 1c Planning](progress/PHASE_1c_QUICK_REFERENCE.md)
- [Task Dependencies](progress/PHASE_1c_DEPENDENCY_DIAGRAM.md)

**Architecture**
- [Scoring Architecture Design](design/Phase_1_Scoring_Architecture.md)
- [Phase 1a Implementation Details](progress/phase-1a/PHASE_1_IMPLEMENTATION.md)

---

**Other Resources**
- [GitHub Repository](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course)
- [Repository README](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course#readme)
```

---

## Implementation Plan

### **Phase 1: Immediate (< 1 hour)**

```
[ ] 1. Add nav_order to 3 QA files
[ ] 2. Enhance QA index.md with table
[ ] 3. Add BRANCH_MERGE_STATUS to progress index
[ ] 4. Add Jekyll note to main index
```

**Effort:** 30 minutes  
**Impact:** High - Makes QA section discoverable

---

### **Phase 2: Short-term (1-2 hours)**

```
[ ] 5. Enhance phase-1a index.md
[ ] 6. Enhance phase-1b index.md
[ ] 7. Enhance design index.md
```

**Effort:** 1 hour  
**Impact:** High - Makes Phase 1a/1b navigable

---

### **Phase 3: Long-term (Optional)**

```
[ ] 8. Create SITE_GUIDE.md (role-based navigation)
[ ] 9. Create LINKS.md (centralized links dashboard)
```

**Effort:** 1-2 hours  
**Impact:** Medium - Improves discoverability for new readers

---

## Success Metrics

After implementing these improvements:

✅ **100% of files have nav_order** (currently some QA/Phase files missing)  
✅ **All index pages list their child documents** (currently sparse)  
✅ **Role-based quick-start guides available** (currently only in progress/)  
✅ **Cross-section references working** (currently disconnected)  
✅ **Jekyll site disclaimer present** (currently absent)  
✅ **New user onboarding time reduced** from 1+ hour to 20-30 minutes

---

## Conclusion

The documentation site has a **solid foundation** with consistent frontmatter and hierarchy. The recommended improvements focus on **discoverability** and **user onboarding**, making it easier for new readers to find relevant content.

**Recommendation:** Implement Priority 1 & 2 improvements immediately (1.5-2 hours total effort) for significant UX improvement.

---

**Generated:** 19 November 2026  
**Author:** Copilot  
**Purpose:** Navigation audit and improvement recommendations
