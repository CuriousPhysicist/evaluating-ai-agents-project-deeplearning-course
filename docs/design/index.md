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
| [CLI and Module Refactoring Strategy](CLI_Module_Refactoring_Strategy.md) | Proactive guidance for anticipated refactoring as code grows | Ongoing |
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

