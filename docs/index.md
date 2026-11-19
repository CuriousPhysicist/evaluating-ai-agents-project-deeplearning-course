---
title: Home
nav_order: 1
permalink: /
---

# Agent Evals

A command-line evaluation harness for a tool-using sales assistant. It records agent runs in local Phoenix, evaluates router and skill behavior separately, measures convergence across similar questions, and compares version results.

| Section | Contents |
| --- | --- |
| [Specification](spec/index.md) | The source spec, resolved decisions, proposed T1-T21 test suite |
| [QA reviews](qa/index.md) | Spec-vs-harness checks, score comparisons, QA refactor plan |
| [Design](design/index.md) | Scoring architecture decisions |
| [Progress records](progress/index.md) | Phase 1a and 1b implementation and completion records |

Installation and usage are in the repository [README](https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course#readme).

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

### New to This Documentation?

[Quick Navigation Guide](SITE_GUIDE.md) →
