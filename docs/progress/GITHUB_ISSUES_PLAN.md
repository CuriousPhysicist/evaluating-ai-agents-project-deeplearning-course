---
title: "GitHub Issues Plan for Phase 1c & Beyond"
parent: Progress records
nav_order: 12
---

# GitHub Issues Templates for Phase 1c & Beyond

**Date:** 19 November 2026  
**Purpose:** Structured tracking of remaining work via GitHub issues  
**All issues link to:** `docs/progress/PHASE_1c_DEPENDENCY_DIAGRAM.md`  
**Status:** Ready to create in GitHub

---

## Overview

This document provides issue templates for creating GitHub issues to track Phase 1c work and future enhancements. Each issue:

- **Stands alone:** Includes scope, deliverables, success criteria
- **Tracks dependencies:** Clear blocking relationships
- **Estimates effort:** Realistic time expectations
- **Includes labels:** For filtering and prioritization
- **Links to documentation:** References supporting design docs

---

## Issue Creation Checklist

Before creating issues in GitHub:

- [ ] All issues have clear titles and descriptions
- [ ] Dependencies are verified (blocks/depends-on)
- [ ] Effort estimates are realistic
- [ ] Success criteria are testable
- [ ] Labels are consistent
- [ ] All reference documentation exists

---

# Phase 1c Critical Priority Issues

## Issue #1: CI/CD Compliance Gating Phase 1 Implementation ✅ MERGED

**Status:** ✅ COMPLETED (Merged 19 Nov 2026)  
**Branch:** `feat_cicd_gating` → `main`  
**Commit:** 41fa063

This has been completed and merged into main. See:
- `docs/progress/phase-1c/CI_CD_GATING_PHASE_1_PROGRESS.md`
- `docs/progress/phase-1c/CI_CD_GATING_PLAN.md`
- `docs/progress/phase-1c/COMPLIANCE_CHECKING_GUIDE.md`

**Deliverables:**
- Exit code contract definition (5 exit codes + enums + exceptions)
- Threshold configuration system (YAML + environment support)
- Compliance checking framework (3 core classes)
- Comprehensive test suite (52 tests, 100% passing)
- Complete documentation

---

# Phase 1c High Priority Issues

## Issue #2: Historical Score Tracking in Phoenix Database

**Title:** Historical Score Tracking: Automatic Experiment Creation & Storage

**Labels:**
- `phase-1c`
- `high-priority`
- `feature`
- `tracking`

**Effort Estimate:** 4-6 days

**Depends On:** 
- Phase 1c CI/CD Gating (Issue #1) ✅ COMPLETE
- Main branch stable

**Blocks:**
- Issue #3 (Dashboard for Trend Visualization)
- Issue #4 (Regression Detection & Alerts)

### Description

Store compliance scores over time in Phoenix database to enable:
- Version-to-version comparison
- Trend analysis across releases
- Historical regression detection
- Dashboard visualization

### Current State

- Phoenix integration exists for manual review snapshots
- Scores can be exported manually
- No automatic storage from test runs
- No historical comparison capability

### Scope

**Automatic Experiment Creation**
- Create Phoenix experiment after test run
- Map test outcomes to compliance scores
- Store per-requirement results
- Retain version metadata (version, timestamp, branch)

**Data Structure**
- Experiments: one per evaluation run
- Results: per-requirement scores
- Metadata: version, timestamp, branch, baseline
- Raw data: individual test outcomes

**Query Support**
- Retrieve scores by version
- Filter by date range
- Compare two versions
- Aggregate across time

### Deliverables

1. Post-test hook integration with Phoenix
2. Experiment creation function with score mapping
3. Data structure design for historical storage
4. Query/retrieval API functions
5. Documentation with examples
6. Integration tests (minimum 10 test cases)

### Success Criteria

- ✅ Experiments automatically created after every test run
- ✅ Per-requirement scores stored in Phoenix
- ✅ Historical data persists across runs
- ✅ Version comparison possible via API
- ✅ Dashboard can query data
- ✅ All tests passing (100% pass rate)
- ✅ Documentation complete with examples

### Additional Notes

- Design baseline-first approach with floating-point tolerance
- Support multiple baseline configurations
- Reference: `docs/progress/PHASE_1c_DEPENDENCY_DIAGRAM.md`

---

## Issue #3: Dashboard for Trend Visualization

**Title:** Create Interactive Dashboard for Compliance Score Trends

**Labels:**
- `phase-1c`
- `medium-priority`
- `feature`
- `visualization`
- `ui`

**Effort Estimate:** 5-7 days

**Depends On:**
- Issue #2 (Historical Score Tracking)

**Blocks:**
- None (optional feature)

### Description

Build visual representation of compliance score evolution using Phoenix, showing per-requirement changes, version comparisons, and trend analysis.

### Scope

**Trend Views:**
- Overall compliance score over time (line chart)
- Per-requirement scores by version (heatmap or table)
- Version comparison side-by-side
- Requirement-specific historical trends
- Regression highlights

**Interactive Features:**
- Date range filtering
- Requirement selection/filtering
- Version comparison picker
- Export/share functionality
- Responsive design (desktop & mobile)

### Deliverables

1. Phoenix dashboard configuration templates
2. Visualization components (charts, tables)
3. Filtering and comparison logic
4. Documentation with screenshots
5. Configuration guide for custom dashboards
6. Integration tests (minimum 10 test cases)

### Success Criteria

- ✅ Dashboard displays trends correctly
- ✅ All filters work as expected
- ✅ Performance acceptable with 1+ years of data
- ✅ Mobile responsive
- ✅ Export functionality works
- ✅ Documentation complete with examples

### Additional Notes

- Use Phoenix's built-in visualization capabilities
- Consider using interactive libraries (e.g., Plotly, Recharts)
- Support customizable themes
- Reference: `docs/progress/PHASE_1c_DEPENDENCY_DIAGRAM.md`

---

## Issue #4: Regression Detection & Alerts

**Title:** Implement Automated Regression Detection with Multi-Channel Alerts

**Labels:**
- `phase-1c`
- `medium-priority`
- `feature`
- `alerts`
- `notifications`

**Effort Estimate:** 3-4 days

**Depends On:**
- Issue #2 (Historical Score Tracking)
- Issue #1 (CI/CD Gating) ✅ COMPLETE

**Blocks:**
- None (optional feature)

### Description

Automatically detect when compliance scores drop and alert via multiple channels (Slack, email, GitHub PR comments).

### Scope

**Detection Logic:**
- Compare current score vs baseline (by version/branch)
- Flag individual requirement score decreases
- Calculate impact magnitude
- Categorize by severity (warning, critical)
- Support configurable thresholds

**Notification Channels:**
- Slack integration (webhook-based)
- Email notifications (optional)
- GitHub PR comments (via GitHub Actions)
- CLI output for local runs

**Configuration:**
- Alert thresholds (per-requirement and overall)
- Notification recipients
- Severity levels and escalation rules
- Enable/disable per channel

### Deliverables

1. Regression detection algorithm
2. Notification integrations (at least 2)
3. Configuration schema (YAML format)
4. Alert templates for each channel
5. Documentation with setup examples
6. Integration tests (minimum 15 test cases)

### Success Criteria

- ✅ Regressions detected correctly
- ✅ Alerts sent to all configured channels
- ✅ No false positives in test data
- ✅ Performance acceptable (< 2 seconds to generate alerts)
- ✅ Configuration documented
- ✅ Setup guide for each channel
- ✅ All tests passing (100% pass rate)

### Additional Notes

- Design with extensibility in mind for future notification channels
- Include rate limiting to prevent alert spam
- Reference: `docs/progress/PHASE_1c_DEPENDENCY_DIAGRAM.md`

---

# Phase 1c Medium Priority Issues

## Issue #5: Address Evidence Gaps in Requirements

**Title:** QA Review & Evidence Gap Closure for 6 Requirements (T10, T12, T13, T18-T20)

**Labels:**
- `phase-1c`
- `medium-priority`
- `qa`
- `testing`

**Effort Estimate:** 2-3 days

**Depends On:**
- None (independent task)

**Blocks:**
- None (improves confidence but not blocking)

### Description

Review and resolve evidence gaps identified in Phase 1b QA review for 6 requirements with weaker or indirect test evidence.

### Requirements in Scope

- **T10:** Router correctly routes to skills
- **T12:** Agent identifies when no tool is appropriate
- **T13:** Agent correctly builds context
- **T18:** Agent version comparison tracking
- **T19:** Offline evaluation reproducibility
- **T20:** Historical result preservation

### Current State

- Tests exist for all 21 requirements
- Some tests provide indirect evidence only
- Confidence levels vary
- T1-T9, T11, T14-T17, T21 all have strong evidence

### Work Items

For each requirement:

1. Analyze current test coverage
2. Assess if gaps are:
   - Test coverage gaps (need more direct tests)
   - Evidence mapping gaps (tests exist but not marked correctly)
   - Specification gaps (requirement needs clarification)
3. Take action:
   - Add new tests to increase coverage
   - Update evidence mappings in `t1-t21-spec.yaml`
   - Clarify requirement definitions
4. Document confidence level
5. Verify new tests passing

### Deliverables

1. Evidence review document per requirement
2. New test cases (if needed)
3. Updated `t1-t21-spec.yaml` with evidence references
4. Confidence level documentation
5. QA sign-off for all 6 requirements

### Success Criteria

- ✅ Each requirement has clear, direct evidence
- ✅ Confidence level documented
- ✅ All new tests added and passing (100% pass rate)
- ✅ Evidence mapping updated
- ✅ No regression in existing tests
- ✅ QA review completed

### Additional Notes

- Can run in parallel with other Phase 1c tasks
- Review existing test suite for reusable patterns
- Document decision for each requirement
- Reference: `docs/progress/OUTSTANDING_TASKS_AND_GAPS.md`

---

## Issue #6: Complete Repository Structure Migration

**Title:** Finish Repository Structure Migration & Documentation

**Labels:**
- `phase-1c`
- `low-priority`
- `documentation`
- `migration`

**Effort Estimate:** 1-2 days

**Depends On:**
- None (mostly complete)

**Blocks:**
- None (documentation/UX improvement)

### Description

Complete the in-progress repository structure migration and create comprehensive migration guide for users with custom configurations.

### Completed Work ✅

- Grouped documentation under `docs/`
- Moved runtime inputs to `inputs/` structure
- Moved compliance spec to `specifications/compliance/`
- Updated code and tests accordingly
- Archived pre-refactor test harness

### Remaining Work

1. **User Migration Guide**
   - Document migration path for customized files
   - Provide examples of common customizations
   - Include mapping table: old path → new path

2. **Legacy Path Warnings**
   - Test that old paths produce helpful error messages
   - Ensure warnings clearly indicate new locations
   - Support deprecation period (if needed)

3. **Final Validation**
   - Scan codebase for hardcoded old paths
   - Update any remaining references
   - Run full test suite

4. **Documentation**
   - Update README with structure explanation
   - Add migration guide section
   - Include FAQ for common questions

### Deliverables

1. Comprehensive migration guide (Markdown)
2. Path mapping reference table
3. Updated README.md
4. Deprecation warnings for legacy paths
5. Test coverage for migration scenarios

### Success Criteria

- ✅ No hardcoded legacy paths in production code
- ✅ Migration guide clear and actionable
- ✅ Warning messages helpful
- ✅ All tests passing
- ✅ Users can easily find files in new locations

### Additional Notes

- Can run in parallel with other tasks
- Reference: `docs/progress/OUTSTANDING_TASKS_AND_GAPS.md`

---

## Issue #7: Jekyll Documentation Site Completion

**Title:** Complete Jekyll Documentation Site & Navigation

**Labels:**
- `phase-1c`
- `low-priority`
- `documentation`
- `site`

**Effort Estimate:** 1-2 days

**Depends On:**
- None (independent)

**Blocks:**
- None (documentation improvement)

### Description

Complete the in-progress Jekyll-based documentation site with full navigation, search, and proper linking of all documentation.

### Current State

- Jekyll site configured
- Basic structure in place
- Some pages linked, others need integration
- Navigation incomplete
- Search functionality possible but not configured

### Work Items

1. **Navigation Setup**
   - Configure main navigation menu
   - Set up breadcrumb navigation
   - Create site map/index
   - Add "Previous/Next" links between related pages

2. **Page Organization**
   - Ensure all Markdown files discoverable
   - Fix any broken internal links
   - Add proper frontmatter to all pages
   - Organize under appropriate categories

3. **Search & Discovery**
   - Enable Jekyll search functionality
   - Configure search index
   - Test search across all pages

4. **Visual Polish**
   - Consistent styling across all pages
   - Responsive design verification
   - Code block formatting
   - Image integration (if needed)

5. **Deployment**
   - Verify local build works
   - Test remote build (GitHub Pages or similar)
   - Confirm site is accessible
   - Add CI/CD job to build on push

### Deliverables

1. Complete navigation menu
2. Linked documentation structure
3. Search functionality
4. CI/CD build configuration
5. Deployment verification
6. User guide for site navigation

### Success Criteria

- ✅ All documentation pages linked and accessible
- ✅ Navigation menu complete and functional
- ✅ Search works across all pages
- ✅ Site builds successfully locally and remotely
- ✅ No broken links
- ✅ Mobile responsive
- ✅ CI/CD integration working

### Additional Notes

- Can run in parallel with other tasks
- Reference: `docs/progress/OUTSTANDING_TASKS_AND_GAPS.md`
- Leverages existing Jekyll setup from Phase 1b

---

# Phase 2 & Beyond - Future Enhancements

## Issue #8: CLI Architecture Separation (Proposal)

**Title:** RFC: Separate Agent Evaluation and Spec Assurance CLI Concerns

**Labels:**
- `phase-2`
- `enhancement`
- `architecture`
- `rfc`

**Status:** 💡 Proposal only  
**Effort Estimate:** 2-3 days (if approved)  
**Timing:** Phase 2 or later

### Description

Proposal to separate CLI concerns between agent evaluation and specification assurance for better modularity and future extraction.

### Current State

- Mixed CLI with both workflows
- Some commands support both features
- Unclear separation of concerns

### Proposed Separation

**Agent Evaluation CLI:**
- `setup` - Prepare environment
- `ask` - Query agent
- `evaluate` - Run full evaluation
- `compare` - Compare results

**Spec Assurance CLI:**
- `assurance` - Run compliance checks
- `assurance-compare` - Compare compliance results

### Benefits

- Clearer separation of concerns
- Easier to extract assurance tool later
- Reduced dependencies for each workflow
- Better documentation of each subsystem

### Approach

**Phase 1:** Internal refactoring (no user-facing changes)
- Create separate CLI handler modules
- Refactor common validation code
- Reorganize command structure

**Phase 2:** Optional separate entry points (if needed)
- Add `spec-assurance` command alongside `agent-evals`
- Maintain compatibility wrappers
- Document both interfaces

**Phase 3:** Extraction (only if high priority)
- Package assurance tool independently
- Support with other specifications

### Status

- Document proposal but no immediate action
- Revisit if extraction becomes high priority
- Collect user feedback

---

## Issue #9: Extract `spec_assurance` as Standalone Package

**Title:** Extract Generic Compliance Scoring Framework as Standalone Package

**Labels:**
- `phase-2`
- `enhancement`
- `extraction`
- `future`

**Status:** 💡 Future product (not started)  
**Effort Estimate:** 3-5 days (after stabilization)  
**Timing:** Phase 2 or later

### Description

Package the specification-agnostic compliance scoring framework for reuse in other projects.

### Current State

- Generic framework design confirmed
- Works with any YAML/JSON specification
- Already supports five-level rubric with configurable weights
- Tightly integrated with current repo

### Value

- Reusable in other projects
- Standalone documentation
- Independent versioning
- PyPI distribution possible

### Path to Extraction

1. **Stabilize** (after Phase 1c)
   - Confirm Phase 1c work is solid
   - Gather user feedback on current design
   - Finalize API and configuration formats

2. **Package**
   - Create separate package structure
   - Separate from agent evaluation code
   - Create standalone repository (if appropriate)

3. **Distribute**
   - Publish to PyPI
   - Create documentation site
   - Provide examples

4. **Support**
   - Version independently
   - Maintain compatibility matrix

### Not Blocking

- Current repo functions independently
- No extraction needed for Phase 1c or 2
- User demand will drive timing

---

## Issue #10: Custom Scoring Functions Per Requirement

**Title:** Support Custom Scoring Logic for Individual Requirements

**Labels:**
- `phase-2`
- `enhancement`
- `feature`
- `future`

**Status:** 💡 Enhancement (not started)  
**Effort Estimate:** 2-3 days  
**Timing:** Phase 2 or later

### Description

Allow users to define custom scoring functions for specific requirements beyond the five-level rubric.

### Proposal

- Override scoring for individual requirements
- Support Python functions or rule-based systems
- Maintain compatibility with generic engine
- Document examples

### Benefits

- Support specialized scoring domains
- Better fit for unique requirements
- Maintain default rubric for most requirements
- Extensible framework

### Implementation Approach

- Configuration hook for custom functions
- Python function support via import
- Validation of custom functions
- Documentation and examples

---

## Issue #11: Webhook Notifications for Integration

**Title:** Add Webhook Support for Custom Integrations

**Labels:**
- `phase-2`
- `enhancement`
- `notifications`
- `future`

**Status:** 💡 Enhancement (not started)  
**Effort Estimate:** 1-2 days  
**Timing:** Phase 2 or later

### Description

Enable webhook notifications for custom integrations beyond Slack/email.

### Scope

- Generic webhook support
- Custom headers and authentication
- Payload templating
- Retry logic

### Benefits

- Support unlimited integrations
- Teams/Discord/Mattermost/etc.
- Custom internal systems
- Flexible payload format

---

## Issue #12: Advanced Filtering & Analysis

**Title:** Add Advanced Filtering and Analysis Tools

**Labels:**
- `phase-2`
- `enhancement`
- `analytics`
- `future`

**Status:** 💡 Enhancement (not started)  
**Effort Estimate:** 2-3 days  
**Timing:** Phase 2 or later

### Description

Provide powerful filtering and analysis capabilities for compliance data.

### Features

- Complex query support (SQL-like or DSL)
- Aggregation functions
- Custom report generation
- Data export formats (CSV, Parquet, etc.)
- Visualization templates

### Benefits

- Power-user data analysis
- Research and reporting
- Compliance audits
- Trend analysis beyond dashboard

---

# Reference Documents

## Dependency Diagram

See: [`docs/progress/PHASE_1c_DEPENDENCY_DIAGRAM.md`](PHASE_1c_DEPENDENCY_DIAGRAM.md)

This document visualizes all dependencies and blocking relationships for Phase 1c work.

## Outstanding Tasks Document

See: [`docs/progress/OUTSTANDING_TASKS_AND_GAPS.md`](OUTSTANDING_TASKS_AND_GAPS.md)

Comprehensive details on all 13 outstanding tasks from the original review.

## Related Documentation

- [Phase 1a & 1b completion](PHASE_1_COMPLETION_RECORD.md)
- [CI/CD Gating Phase 1](phase-1c/CI_CD_GATING_PHASE_1_PROGRESS.md)
- [Repository structure](repository-structure.md)
- [Quick reference](PHASE_1c_QUICK_REFERENCE.md)

---

## How to Create GitHub Issues

### Manual Process

1. Go to GitHub repository: https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course
2. Navigate to Issues tab
3. Click "New Issue" button
4. For each issue:
   - Copy title from this document
   - Copy description sections into issue body
   - Add labels from "Labels:" section
   - Leave unassigned initially
   - Create issue

### Automated Process (Future)

Consider using GitHub CLI or Actions to automate issue creation from this template.

---

## Issue Tracking Best Practices

1. **Assign Issues:** Assign to team members based on skills
2. **Link PRs:** Link pull requests when work starts
3. **Update Status:** Move issues through columns as work progresses
4. **Dependencies:** Use "Depends on" project field or comments
5. **Milestones:** Group related issues into milestones
6. **Reviews:** Add code review requests when PR is ready

---

**Created:** 19 November 2026  
**Updated:** 19 November 2026  
**Author:** Copilot  
**Purpose:** GitHub issues template for Phase 1c & Beyond tracking  
**Status:** Ready to create in GitHub
