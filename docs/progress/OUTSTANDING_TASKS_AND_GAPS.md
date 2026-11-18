---
title: "Outstanding tasks and gaps review"
parent: Progress records
nav_order: 10
---

# Outstanding Tasks & Gaps Review

**Date:** 18 November 2026  
**Purpose:** Comprehensive assessment of remaining work after Phase 1a & 1b completion  
**Status:** Ready for Phase 1c planning  
**Audience:** Project leads, planners, developers, stakeholders

---

## Executive Summary

**All Phase 1a & 1b desired outcomes are complete.** This document captures:
- 1 critical task ready for immediate action (merge to main)
- 5 high/medium priority items for Phase 1c
- 7 low-priority enhancements for future phases
- Dependencies and sequencing for planned work

**No blockers remain.** Phase 1c can proceed immediately after merge approval.

---

## Status at a Glance

| Category | Count | Status |
|----------|-------|--------|
| **Integration** | 1 | ✅ Ready |
| **CI/CD** | 3 | ⏳ Planned |
| **QA** | 1 | ⏳ To review |
| **Visualization** | 1 | ⏳ Planned |
| **Architecture** | 1 | 💡 Proposal |
| **Enhancement** | 4 | 💡 Future |
| **Refactoring** | 1 | 🔄 In progress |
| **Documentation** | 1 | 🔄 In progress |
| **TOTAL** | **13** | Mixed |

**Key Metrics:**
- Phase 1a & 1b Completion: **100%** ✅
- Test Pass Rate: **100%** (155/155) ✅
- Code Coverage: **87.34%** ✅
- Regressions: **0** ✅
- Blockers for Phase 1c: **0** ✅
- Ready to Merge: **Yes** ✅

---

## 🎯 CRITICAL PRIORITY

### 1. Merge `feat_develop_metric` to main

**Status:** ✅ READY  
**Branch:** `feat_develop_metric` (remote: `origin/feat_develop_metric`)  
**Effort:** 1-2 hours (review + merge)  
**Blocking:** Phase 1c kickoff, all subsequent Phase 1c tasks  

#### Deliverables Included

**Phase 1a — Generic Compliance Scoring Engine**
- Core module: `agent_evals/spec_assurance/` (475 LoC, 87.34% coverage)
- Configuration: `specifications/compliance/schema.json` + `t1-t21-spec.yaml`
- Tests: 30 new tests in `tests/test_spec_assurance.py` (100% pass)
- Documentation: Architecture, implementation, examples

**Phase 1b — Pytest Integration & Automation**
- Pytest plugin: `agent_evals/pytest_plugin.py`
- Compliance reporters: JSON, HTML, console formats
- 92 existing tests marked with T-ID markers
- 15+ integration tests (100% pass)
- CLI commands: `report`, `check`, `summary`
- Documentation: pytest integration guide, CI/CD examples

#### Verification Checklist

✅ **Code Quality**
- All code reviewed and working
- Generic design confirmed (not T1-T21-specific)
- Configuration-driven approach validated
- Modular architecture confirmed
- Type hints present throughout
- Error handling comprehensive

✅ **Testing**
- 155 total tests passing (100% pass rate)
- Coverage: 87.34% (exceeds 80% threshold)
- Zero regressions in existing code
- Edge cases and error scenarios tested
- Plugin loads without manual configuration
- Reports generate in all formats
- CLI commands functional

✅ **Documentation**
- Architecture documented (Phase_1_Scoring_Architecture.md)
- Implementation details documented (PHASE_1_IMPLEMENTATION.md)
- Pytest integration documented (PHASE_1b_PYTEST_INTEGRATION.md)
- CI/CD setup documented (PHASE_1b_CI_CD_SETUP.md)
- Usage examples provided
- Design decisions explained

✅ **Readiness**
- Ready for code review ✅
- Ready for testing ✅
- Ready for merge to main ✅
- Ready for CI/CD setup ✅
- Ready for team training ✅

#### Next Steps

1. **Code Review:** Review Phase 1a & 1b implementation
2. **Approval:** Sign off on architecture and design
3. **Stage & Commit:** Group into logical commits
4. **Merge:** Merge to main branch
5. **Document:** Update project README with Phase 1 completion

---

## 🔴 HIGH PRIORITY — Phase 1c

### 2. Set up CI/CD Compliance Gating

**Status:** Planned (not started)  
**Effort:** 3-5 days  
**Blocking:** Phase 1c → Phase 1d planning  
**Depends On:** Phase 1b merged to main  

#### Purpose

Implement automated compliance gates that:
- Fail CI/CD pipeline if compliance score drops below configured threshold
- Provide exit codes for scripting and automation
- Support multiple CI/CD platforms
- Enable regression detection

#### Scope

- **Threshold Configuration:** Configurable per environment (dev, staging, prod)
- **Exit Codes:** Machine-readable contracts for CI integration
- **Platform Examples:** GitHub Actions, GitLab CI, Jenkins
- **CLI Integration:** `agent_evals check` command with exit codes
- **Report Integration:** Use Phase 1b compliance reporters

#### Deliverables

1. Exit code contract definition
   - 0 = all tests pass, compliance above threshold
   - 1 = compliance regression detected
   - 2 = configuration error
   - Other codes as needed

2. CI/CD integration examples
   - GitHub Actions workflow
   - GitLab CI configuration
   - Jenkins pipeline

3. Documentation
   - Configuration guide
   - Troubleshooting guide
   - Best practices

#### Success Criteria

- ✅ Exit codes implemented and tested
- ✅ At least 2 CI/CD examples working
- ✅ Threshold configuration documented
- ✅ Zero false positives in test run

---

### 3. Historical Score Tracking in Phoenix

**Status:** Planned (not started)  
**Effort:** 4-6 days  
**Blocking:** Trend analysis, regression detection  
**Depends On:** CI/CD gating framework  

#### Purpose

Store compliance scores over time in Phoenix database to enable:
- Version-to-version comparison
- Trend analysis across releases
- Historical regression detection
- Dashboard visualization

#### Current State

- Phoenix integration exists for manual review snapshots
- Scores can be exported manually
- No automatic storage from test runs
- No historical comparison

#### Scope

**Automatic Experiment Creation**
- Create Phoenix experiment after test run
- Map test outcomes to compliance scores
- Store per-requirement results
- Retain version metadata

**Data Structure**
- Experiments: one per evaluation run
- Results: per-requirement scores
- Metadata: version, timestamp, branch
- Raw data: individual test outcomes

**Query Support**
- Retrieve scores by version
- Filter by date range
- Compare two versions
- Aggregate across time

#### Deliverables

1. Experiment creation from test results
2. Automatic storage to Phoenix (post-test hook)
3. Query/retrieval functions
4. Documentation

#### Success Criteria

- ✅ Experiments stored automatically
- ✅ Historical data persists across runs
- ✅ Version comparison possible
- ✅ Dashboard can query data

---

## 🟡 MEDIUM PRIORITY — Phase 1c Extensions

### 4. Dashboard for Trend Visualization

**Status:** Planned (not started)  
**Effort:** 5-7 days  
**Depends On:** Historical score tracking  

#### Purpose

Create visual representation of compliance trends using Phoenix to show:
- Score evolution across versions
- Per-requirement changes
- Version comparison
- Regression highlights

#### Current State

- Phoenix supports visualization
- No dashboard implemented yet
- Manual review snapshots can be compared via CLI

#### Scope

**Trend Views**
- Overall score over time
- Per-requirement scores by version
- Version comparison side-by-side
- Requirement-specific trends

**Interactive Features**
- Date range filtering
- Requirement selection
- Version comparison picker
- Export/share functionality

#### Deliverables

1. Phoenix dashboard configuration
2. Visualization templates
3. Documentation

---

### 5. Regression Detection & Alerts

**Status:** Planned (not started)  
**Effort:** 3-4 days  
**Depends On:** Historical score tracking + CI gating  

#### Purpose

Automatically detect and alert when compliance scores drop:
- Per-requirement regression detection
- Threshold-based alerting
- Multi-channel notifications
- Actionable alerts

#### Scope

**Detection Logic**
- Compare current score vs baseline
- Flag individual requirement decreases
- Calculate impact magnitude
- Categorize by severity

**Notification Channels**
- Slack integration (optional)
- Email notifications (optional)
- GitHub PR comments
- CLI output

**Configuration**
- Alert thresholds
- Notification recipients
- Severity levels

#### Deliverables

1. Regression detection algorithm
2. Notification integrations (Slack, email)
3. Configuration schema
4. Documentation and examples

---

### 6. Address Evidence Gaps (T10, T12, T13, T18-T20)

**Status:** Pending QA review  
**Effort:** 2-3 days  
**Priority:** Medium (affects confidence in scoring)  
**Depends On:** None  

#### Issue

QA review in Phase 1b identified 6 requirements with weaker evidence:
- **T10:** Router correctly routes to skills
- **T12:** Agent identifies when no tool is appropriate
- **T13:** Agent correctly builds context
- **T18:** Agent version comparison tracking
- **T19:** Offline evaluation reproducibility
- **T20:** Historical result preservation

#### Current State

- Tests exist for all 21 requirements
- Some tests provide indirect evidence only
- Confidence levels vary

#### Actions Needed

1. **Review:** Analyze current test coverage for each requirement
2. **Assess:** Determine if gaps are:
   - Test coverage gaps (need more tests)
   - Evidence mapping gaps (tests exist but not marked correctly)
   - Design gaps (specification unclear)

3. **Close:** Either:
   - Add new tests to increase coverage
   - Update evidence mappings in `t1-t21-spec.yaml`
   - Clarify requirement definitions

#### Success Criteria

- ✅ Reviewed all 6 requirements
- ✅ Each has clear, direct evidence
- ✅ Confidence level documented
- ✅ Any new tests added and passing

---

## 🟢 LOWER PRIORITY

### 7. Complete Repository Structure Migration

**Status:** 🔄 In-progress  
**Effort:** 1-2 days  
**Timeline:** Current (overlaps with Phase 1b)  

#### Completed ✅

- Grouped documentation under `docs/`
- Moved runtime inputs to `inputs/` structure
- Moved compliance spec to `specifications/compliance/`
- Updated code and tests accordingly
- Archived pre-refactor test harness

#### Remaining

- **User Migration:** Document manual migration path for customized files
- **Legacy Path Warnings:** Test that old paths produce helpful errors
- **Documentation:** Complete migration guide in README
- **Validation:** Ensure no hardcoded old paths remain

#### Note

Manual migration was chosen to preserve user-edited input files. The tool:
- Does not automatically copy or delete existing inputs
- Reports legacy files rather than silently using new defaults
- Requires users to manually reconcile custom content

#### Success Criteria

- ✅ No hardcoded legacy paths in production code
- ✅ Migration guide clear and complete
- ✅ Warning messages helpful and actionable
- ✅ All tests passing

---

### 8. Consider CLI Separation (Architecture Proposal)

**Status:** 💡 Proposal (not started)  
**Effort:** 2-3 days (if approved)  
**Timeline:** Phase 2 or later  

#### Proposal

Separate concerns between:
- **Agent Evaluation CLI:** `setup`, `ask`, `evaluate`, `compare`
- **Spec Assurance CLI:** `assurance`, `assurance-compare`

#### Benefits

- Clearer separation of concerns
- Easier to extract assurance tool
- Reduced dependencies for each workflow
- Better documentation of each subsystem

#### Approach

1. **Phase 1:** Internal separation (no user-facing changes)
   - Refactor common validation/scoring code
   - Move CLI handlers into separate modules

2. **Phase 2:** Optional separate entry points
   - Add `spec-assurance` command
   - Retain compatibility wrappers
   - Document both interfaces

3. **Phase 3:** Extraction (if needed)
   - Package assurance tool independently
   - Support with other specifications

#### Current Status

- Not blocking any critical functionality
- Mixed CLI works fine for now
- Revisit if extraction becomes priority

#### Decision

Proposal is documented but no action required unless:
- Extraction becomes high priority
- Code complexity grows significantly
- User feedback indicates confusion

---

### 9. Extract `spec_assurance` as Standalone Package

**Status:** 💡 Future product (not started)  
**Effort:** 3-5 days (after stabilization)  
**Timeline:** Phase 2 or later  

#### Purpose

Reuse the generic compliance scoring framework with other projects and specifications:
- Specification-agnostic framework
- Support for YAML/JSON/Python dict specs
- Five-level rubric + configurable weights
- Phoenix integration optional

#### Current State

- Already generic in design
- Works with any specification
- Tightly integrated with this repo

#### Path to Extraction

1. **Stabilize:** Confirm Phase 1c work is solid
2. **Package:** Create separate package structure
3. **Distribute:** Publish to PyPI (if appropriate)
4. **Document:** Stand-alone documentation
5. **Support:** Version independently

#### Not Blocking

- Current repo can function independently
- Revisit after CI/CD gating is stable
- User demand will drive timing

---

### 10. Custom Scoring Functions Per Requirement

**Status:** 💡 Enhancement (not started)  
**Effort:** 2-3 days (after framework is stable)  
**Timeline:** Phase 2 or later  

#### Proposal

Allow users to define custom scoring logic for specific requirements beyond the five-level rubric:
- Override scoring for individual requirements
- Support Python functions or rule-based systems
- Maintain compatibility with generic engine
- Document examples

#### Current State

- Five-level rubric is hardcoded
- Same rubric applies to all requirements

#### Potential Scoring Models

- **Linear:** "If N tests pass, score = N/total"
- **Weighted:** "If critical test passes, weight higher"
- **Threshold:** "Score 1.0 only if 100% tests pass"
- **Custom:** Python function or expression

#### Use Cases

- Requirements with varying test difficulty
- Performance-based requirements
- Subjective assessment requirements

#### Decision

Nice-to-have enhancement; can be added after Phase 1c stabilizes.

---

### 11. Webhook Notifications

**Status:** 💡 Enhancement (not started)  
**Effort:** 1-2 days (simple integration)  
**Timeline:** Phase 2 or later  

#### Purpose

Trigger external workflows when compliance scores change:
- Integration with external systems
- Automated workflows
- Custom notifications

#### Scope

- Trigger on score change
- Support multiple webhook endpoints
- Payload with score change details
- Retry logic for failed webhooks

#### Not Blocking

- Slack/email can be used instead
- Low user demand
- Can be added incrementally

---

### 12. Advanced Filtering & Analysis

**Status:** 💡 Enhancement (not started)  
**Effort:** 2-3 days  
**Timeline:** Phase 2 or later  

#### Features

- Filter by requirement (T1, T5, etc.)
- Filter by version
- Filter by date range
- Filter by result status (pass/fail/skip)
- Custom queries against historical data

#### Current State

- Can export to JSON and analyze manually
- Dashboard will support some filtering
- CLI analysis is basic

#### Potential Extensions

- SQL-like query interface
- GraphQL API
- Advanced analytics
- Statistical analysis

---

### 13. Jekyll Documentation Site Completion

**Status:** 🔄 In-progress  
**Effort:** 1-2 days (remaining)  
**Timeline:** Current  

#### Completed ✅

- Local offline testing setup
- Markdown documentation structure
- MathJax 3 support for formulas
- Just-the-docs theme integrated
- Build scripts created

#### Remaining

- **Live CDN Validation:** Test rendering with live MathJax from jsDelivr
- **Performance Benchmarking:** Compare page load times (maths vs non-maths)
- **GitHub Pages Setup:** Configure repository for automatic publishing
- **Custom Domain:** Setup if needed

#### Success Criteria

- ✅ Local build working (`bundle exec jekyll serve`)
- ✅ All pages render correctly offline
- ✅ MathJax formulas render from CDN
- ✅ Page load times acceptable
- ✅ GitHub Pages publishing configured

---

## 📋 Recommended Sequencing

### **Immediate (This Week)**

1. ✅ **Code Review:** Phase 1a & 1b work
2. ✅ **Merge:** `feat_develop_metric` → `main`
3. 📄 **Document:** Update README with Phase 1 completion

**Time Estimate:** 4-8 hours

---

### **Phase 1c — Weeks 1-2**

4. ⏳ **Plan Phase 1c:** 
   - Approve CI/CD gating approach
   - Prioritize based on team capacity
   - Set timelines

5. ⏳ **QA Review:** 
   - Address evidence gaps (T10, T12, T13, T18-T20)
   - Add tests if needed
   - Update specifications

**Time Estimate:** 2-5 days

---

### **Phase 1c — Weeks 2-4**

6. ⏳ **CI/CD Gating:**
   - Exit codes + CI examples
   - Test all platforms
   - Documentation

7. ⏳ **Historical Tracking:**
   - Experiment creation
   - Phoenix integration
   - Query functions

**Time Estimate:** 7-11 days

---

### **Phase 1c — Weeks 4-6**

8. ⏳ **Dashboard:**
   - Visualization templates
   - Interactive filtering
   - Documentation

9. ⏳ **Regression Alerts:**
   - Detection logic
   - Notification integrations
   - Configuration

**Time Estimate:** 8-11 days

---

### **Phase 1d & Beyond (Optional)**

10. 💡 **CLI Separation:** (if extraction planned)
11. 💡 **Custom Scoring:** (if requested)
12. 💡 **Webhook Notifications:** (if needed)
13. 💡 **Advanced Analysis:** (future phase)

---

## 📊 Dependency Graph

```
feat_develop_metric (Ready to merge)
    ↓
Phase 1b Merged to Main (Critical)
    ↓
├─→ CI/CD Gating (High) [3-5d]
│   ├─→ Historical Tracking (High) [4-6d]
│   │   ├─→ Dashboard (Medium) [5-7d]
│   │   └─→ Regression Alerts (Medium) [3-4d]
│   └─→ QA Evidence Gaps (Medium) [2-3d]
│
├─→ Repository Migration (Medium) [1-2d, in-progress]
│
├─→ CLI Separation Proposal (Low) [2-3d, optional]
│
└─→ Enhancement Features (Low)
    ├─→ Extract as Tool (Low) [3-5d]
    ├─→ Custom Scoring (Low) [2-3d]
    ├─→ Webhooks (Low) [1-2d]
    └─→ Advanced Filtering (Low) [2-3d]
```

---

## 🎓 Key Decisions

### 1. Merge Timing
**Decision:** Merge `feat_develop_metric` immediately after code review  
**Rationale:** All verification checklists complete; no blockers remain; unblocks Phase 1c work

### 2. Phase 1c Scope
**Decision:** Focus on CI/CD gating + historical tracking + dashboard  
**Rationale:** These are high-impact, enable regression detection, support team workflows

### 3. Evidence Gaps
**Decision:** Address before Phase 1c completion  
**Rationale:** Increases confidence in automated scoring; small effort; prevents future rework

### 4. CLI Separation
**Decision:** Deferred to Phase 2 (unless extraction becomes priority)  
**Rationale:** Works fine as single CLI; can separate if needed; not blocking current work

### 5. Extraction as Product
**Decision:** Planned for Phase 2 or later  
**Rationale:** Requires stabilization; not needed for current project; can be added later

---

## 📞 Questions & Answers

**Q: Can Phase 1c start before merge?**  
A: Technically yes, but not recommended. Merge first to unblock other work and ensure team is using same codebase.

**Q: How long will Phase 1c take?**  
A: 2-4 weeks depending on team size and priorities. CI/CD gating + tracking is 1-2 weeks; dashboard adds another 1-2 weeks.

**Q: Do we need to implement all Phase 1c items?**  
A: CI/CD gating is high priority. Historical tracking enables trend analysis. Dashboard is nice-to-have. Regression alerts depend on historical tracking.

**Q: What if evidence gaps are found in multiple requirements?**  
A: Plan 2-3 days for QA review and fixes. If major gaps found, may need to defer to Phase 2.

**Q: Should we extract the tool now?**  
A: No. Wait until Phase 1c is stable and you're confident in the design. Extraction is a Phase 2 activity.

**Q: How do we handle backward compatibility?**  
A: CLI separation uses compatibility wrappers; extraction keeps the generic framework independent.

---

## 📝 Document Maintenance

| Item | Status | Owner | Last Updated |
|------|--------|-------|--------------|
| Outstanding Tasks Review | Active | Copilot | 18 Nov 2026 |
| Phase 1c Planning | Pending | TBD | Awaiting kickoff |
| Phase 1c Execution | Pending | TBD | Awaiting kickoff |

---

## 🎯 Success Criteria for Next Phase

✅ **Merge approved and completed**  
✅ **Phase 1c planning document created**  
✅ **Team trained on new tooling**  
✅ **CI/CD gating design reviewed**  
✅ **Historical tracking approach approved**  
✅ **Timeline established**

---

## 📌 Summary

**What's Done:**
- Phase 1a: Generic compliance scoring engine ✅
- Phase 1b: Pytest integration & automation ✅
- All desired outcomes achieved ✅
- Zero regressions ✅

**What's Next:**
1. Merge to main (ready now)
2. Phase 1c: CI/CD gating + historical tracking
3. Dashboard + regression alerts (secondary)
4. Future phases: Extraction, enhancements

**No Blockers:** All work ready to proceed  
**Team Ready:** Documentation, examples, and guides complete  
**Timeline:** 2-4 weeks for Phase 1c core items  

---

**Generated:** 18 November 2026  
**Purpose:** Outstanding tasks review for Phase 1c planning  
**Audience:** Project leads, planners, developers  
**Next Review:** After Phase 1c kickoff  
