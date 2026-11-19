---
title: "Site Navigation Guide"
nav_order: 6
---

# Agent Evals Documentation Site Guide

**Welcome!** This guide helps you navigate the documentation based on your role.

---

## 🎯 Quick Navigation by Role

### I want to understand what was built (Project Leads)
1. Start: [docs/ Home](index.md) - overview
2. Read: [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - summary
3. Dive deeper: [Phase 1a Docs](progress/phase-1a/index.md) & [Phase 1b Docs](progress/phase-1b/index.md)

**Time:** 20-30 minutes

---

### I want to review the code (Code Reviewers)
1. Start: [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - verification checklists
2. Read: [Phase 1a Implementation](progress/phase-1a/PHASE_1_IMPLEMENTATION.md)
3. Review: [QA Checks](qa/index.md) for coverage analysis

**Time:** 30-45 minutes

---

### I'm planning Phase 1c work (Planners)
1. Start: [Phase 1c Quick Reference](progress/PHASE_1c_QUICK_REFERENCE.md) - overview
2. Read: [Outstanding Tasks & Gaps](progress/OUTSTANDING_TASKS_AND_GAPS.md) - details
3. Plan: [Dependency Diagram](progress/PHASE_1c_DEPENDENCY_DIAGRAM.md) - sequencing

**Time:** 30-40 minutes

---

### I want to understand the requirements (Developers)
1. Start: [Specification](spec/index.md) - the requirements
2. Read: [QA Checks](qa/index.md) - coverage analysis
3. Reference: [Design Decisions](design/index.md) - why we built it this way

**Time:** 1-2 hours

---

### I want to use the tool in CI/CD (DevOps)
1. Start: [Phase 1b CI/CD Setup](progress/phase-1b/PHASE_1b_CI_CD_SETUP.md) - examples
2. Read: [Pytest Integration](progress/phase-1b/PHASE_1b_PYTEST_INTEGRATION.md) - how it works
3. Reference: [Phase 1b Plan](progress/phase-1b/PHASE_1b_PLAN.md) - design decisions

**Time:** 30 minutes

---

### I want architecture details (Architects)
1. Start: [Design](design/index.md) - high level
2. Read: [Scoring Architecture](design/Phase_1_Scoring_Architecture.md) - decisions
3. Deep dive: [Phase 1a Implementation](progress/phase-1a/PHASE_1_IMPLEMENTATION.md) - details

**Time:** 1 hour

---

## 📚 Documentation Sections

| Section | Contains | Start Here |
|---------|----------|-----------|
| [Specification](spec/index.md) | Requirements, decisions, test design | For understanding "what" |
| [QA Reviews](qa/index.md) | Coverage analysis, score comparisons | For validation |
| [Design](design/index.md) | Architecture decisions | For understanding "why" |
| [Progress](progress/index.md) | Implementation and planning records | For "current status" |

---

## 🗂️ File Organization

- **docs/spec/** - Original requirements and test suite design
- **docs/qa/** - Quality assurance checks and evidence analysis
- **docs/design/** - Architectural decisions
- **docs/progress/** - Implementation progress
  - **phase-1a/** - Scoring engine implementation
  - **phase-1b/** - Pytest integration implementation
  - **OUTSTANDING_TASKS_AND_GAPS.md** - What's next (Phase 1c & beyond)
  - **PHASE_1c_DEPENDENCY_DIAGRAM.md** - Task sequencing and dependencies
  - **PHASE_1c_QUICK_REFERENCE.md** - One-page Phase 1c overview
  - **BRANCH_MERGE_STATUS.md** - Branch verification and cleanup record

---

## 🌟 Popular Pages

**Most viewed:**
- [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - What was delivered
- [Outstanding Tasks & Gaps](progress/OUTSTANDING_TASKS_AND_GAPS.md) - What's next
- [Pytest Integration Guide](progress/phase-1b/PHASE_1b_PYTEST_INTEGRATION.md) - How to use
- [Phase 1c Dependency Diagram](progress/PHASE_1c_DEPENDENCY_DIAGRAM.md) - Task planning

**New to the project:**
- [Site Navigation Guide](SITE_GUIDE.md) ← You are here
- [Home](index.md)
- [Specification](spec/index.md)

---

## 📱 On Mobile?

Jekyll's Just-the-docs theme works on mobile. Use the ☰ menu at top-left to navigate.

---

## 🔍 How to Search

**Within this site:**
- Use Ctrl+F (Windows) or Cmd+F (Mac) to search text on the current page

**Across the repository:**
- Use GitHub's code search at the [repository](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course)

---

## ❓ Common Questions

**Q: Where's the code?**  
A: Implementation is in the main repository. This documentation site explains what was built and how to use it. [Go to repository →](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course)

**Q: How do I install and run this?**  
A: See the [repository README](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course#readme) for setup instructions.

**Q: What's Phase 1c?**  
A: Next phase of work after Phase 1a & 1b. See [Outstanding Tasks](progress/OUTSTANDING_TASKS_AND_GAPS.md) for details.

**Q: How do I use this in CI/CD?**  
A: See [CI/CD Setup](progress/phase-1b/PHASE_1b_CI_CD_SETUP.md) for examples.

**Q: Is the scoring engine reusable?**  
A: Yes! It's generic and configuration-driven. See [Architecture](design/Phase_1_Scoring_Architecture.md).

---

## 🎓 Learning Paths

### **Path 1: Understand the Product (1-2 hours)**
1. [Specification](spec/index.md) - What was asked
2. [Design](design/index.md) - Why it was designed that way
3. [Phase 1 Completion Record](progress/PHASE_1_COMPLETION_RECORD.md) - What was built

### **Path 2: Use in Development (45 minutes)**
1. [Repository README](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course#readme) - Install & setup
2. [Pytest Integration](progress/phase-1b/PHASE_1b_PYTEST_INTEGRATION.md) - Write tests
3. [Quick Reference](progress/phase-1a/QUICK_REFERENCE.md) - Feature overview

### **Path 3: Integrate with CI/CD (1 hour)**
1. [CI/CD Setup](progress/phase-1b/PHASE_1b_CI_CD_SETUP.md) - Examples
2. [Architecture](design/Phase_1_Scoring_Architecture.md) - How it works
3. [Plan & Design](progress/phase-1b/PHASE_1b_PLAN.md) - Design decisions

### **Path 4: Extend the Tool (2-3 hours)**
1. [Architecture](design/Phase_1_Scoring_Architecture.md) - Design
2. [Implementation](progress/phase-1a/PHASE_1_IMPLEMENTATION.md) - Details
3. [Specification](spec/index.md) - Requirements
4. [QA Checks](qa/index.md) - Coverage/validation

---

## 💡 Navigation Tips

**Stuck?** Try these:
1. Use the sidebar to browse sections
2. Look for quick-start guides at the top of each section
3. Use Ctrl+F to search for specific terms
4. Check the "See Also" links at the bottom of pages

**Want to contribute?** Visit the [GitHub repository](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course) to open issues or PRs.

---

**Next Step:** Choose your role above and jump to the right starting point! →

---

**Last updated:** 19 November 2026  
**Purpose:** Navigation guide for Agent Evals documentation site
