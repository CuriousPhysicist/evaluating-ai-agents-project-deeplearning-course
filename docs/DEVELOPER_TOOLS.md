---
title: "Developer Tools & Optional Utilities"
nav_order: 7
---

# Developer Tools & Optional Utilities

**Last Updated:** 19 November 2026  
**Purpose:** Guide for optional tools and utilities useful for development and repo management  
**Audience:** Contributors, maintainers, CI/CD engineers

---

## Overview

This document catalogs optional tools and utilities that can enhance development workflows. None are required for core project work, but they provide value for specific tasks.

---

## GitHub CLI (`gh`)

### Purpose
Command-line interface for GitHub workflows. Useful for automation, scripting, and bulk operations.

### When to Use
✅ **Recommended for:**
- Automation scripts (issue creation, closing, labeling)
- CI/CD pipelines that need to manage GitHub resources
- Bulk operations (archiving issues, managing projects)
- Advanced GitHub workflows
- Team members who prefer CLI workflows

❌ **Not needed for:**
- One-time issue creation (use web UI)
- Simple PR operations
- Basic repo management

### Installation

**Windows (via Scoop or Chocolatey):**
```powershell
# Using Scoop
scoop install gh

# Using Chocolatey
choco install gh
```

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
apt-get install gh

# Fedora/RHEL
dnf install gh
```

**Verify Installation:**
```bash
gh --version
```

### Authentication

```bash
# Interactive login
gh auth login

# Follow prompts:
# - Choose GitHub.com (default)
# - Choose SSH or HTTPS (SSH recommended)
# - Paste personal access token or generate new
```

**Token Scopes Needed:**
- `repo` - Full control of repositories
- `gist` - Create gists
- `workflow` - Manage workflows

### Common Commands

```bash
# View issues
gh issue list --label "phase-1c"

# Create an issue
gh issue create --title "My Issue" --body "Description"

# Close an issue
gh issue close <number>

# Add label to issue
gh issue edit <number> --add-label "enhancement"

# View pull requests
gh pr list

# Check status of current branch
gh status
```

### Example: Bulk Issue Creation Script

If you create a script to generate issues from templates, it might look like:

```bash
#!/bin/bash
# create_phase1c_issues.sh

# Phase 1c High Priority Issues
gh issue create --title "Historical Score Tracking: Automatic Experiment Creation & Storage" \
  --body "$(cat templates/issue_2_historical_tracking.md)" \
  --label "phase-1c,high-priority,feature"

gh issue create --title "Create Interactive Dashboard for Compliance Score Trends" \
  --body "$(cat templates/issue_3_dashboard.md)" \
  --label "phase-1c,medium-priority,feature,visualization"

# ... more issues
```

### Documentation
- Official docs: https://cli.github.com/manual
- GitHub Learning: https://www.youtube.com/githubuniversity

### When to Add This

**Current Status:** ✅ Optional  
**Add to docs when:** Automation scripts are created  
**Add to project when:** CI/CD pipeline needs GitHub management

---

## PyGithub - Python GitHub API Wrapper

### Purpose
Python library for programmatic GitHub interaction. Better for Python-integrated workflows.

### When to Use
✅ **Recommended for:**
- Python scripts within the repo
- Issue/PR automation in Python
- Integration with evaluation pipeline
- CI/CD workflows written in Python
- Complex GitHub interactions

❌ **Not needed for:**
- Simple one-off operations
- Developer workflows
- Manual GitHub interaction

### Installation

```bash
# Already included in development dependencies (future)
pip install PyGithub

# Or add to pyproject.toml:
[project.optional-dependencies]
github = ["PyGithub>=2.1.1"]

pip install -e ".[github]"
```

### Basic Usage

```python
from github import Github

# Authenticate with token
g = Github(os.environ['GITHUB_TOKEN'])

# Get repository
repo = g.get_repo("CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course")

# Create an issue
issue = repo.create_issue(
    title="My Issue",
    body="Detailed description",
    labels=["phase-1c", "enhancement"]
)

# List issues with filter
for issue in repo.get_issues(state='open', labels=['phase-1c']):
    print(issue.number, issue.title)

# Close an issue
issue.edit(state='closed')
```

### Example: Issue Template Automation

```python
# create_issues_from_yaml.py
import yaml
from github import Github
from pathlib import Path

def load_issue_templates(yaml_file):
    with open(yaml_file) as f:
        return yaml.safe_load(f)

def create_issues(repo, templates):
    for issue_template in templates:
        repo.create_issue(
            title=issue_template['title'],
            body=issue_template['body'],
            labels=issue_template['labels']
        )

if __name__ == "__main__":
    g = Github(os.environ['GITHUB_TOKEN'])
    repo = g.get_repo("CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course")
    
    templates = load_issue_templates("issues.yaml")
    create_issues(repo, templates)
```

### Documentation
- PyGithub docs: https://pygithub.readthedocs.io/
- GitHub REST API: https://docs.github.com/en/rest

### When to Add This

**Current Status:** ✅ Optional  
**Add to pyproject.toml when:**
1. Issue automation becomes needed (Phase 2+)
2. CI/CD pipeline needs GitHub integration
3. Evaluation pipeline needs to create/close issues

---

## Development Environment Tools

### Virtual Environment Management

**Using venv (built-in, recommended):**
```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate.bat     # Windows
```

**Using uv (faster alternative):**
```bash
# Install uv
pip install uv

# Create environment
uv venv
source .venv/bin/activate
```

### Python Version Management

**Using pyenv (manage multiple Python versions):**
```bash
# Install
# macOS: brew install pyenv
# Linux: See https://github.com/pyenv/pyenv

# Install specific Python version
pyenv install 3.11.0

# Set for this project
pyenv local 3.11.0

# Verify
python --version
```

### Linting & Code Quality

**Already integrated:**
- pytest - Testing framework
- Pylance - Type checking (VS Code)

**Optional additions (consider for Phase 2):**
```bash
# Install
pip install black flake8 mypy isort

# Format code
black .

# Lint
flake8 .

# Type check
mypy agent_evals/

# Sort imports
isort .
```

---

## Documentation Tools

### Jekyll (Markdown to HTML site)

**Status:** ✅ Already configured for `docs/` folder

**Local development:**
```bash
# Install Ruby (macOS)
brew install ruby

# Install Jekyll
gem install bundler jekyll

# Navigate to docs folder
cd docs

# Run local server
bundle exec jekyll serve

# View at: http://localhost:4000
```

**Configuration:** `docs/_config.yml`

---

## CI/CD Tools

### GitHub Actions

**Status:** ✅ Already integrated

**Configuration files:**
- `.github/workflows/*.yml` - Action definitions
- See: `docs/progress/phase-1c/CI_CD_GATING_PLAN.md` for details

### Local GitHub Actions Testing

**act - Run GitHub Actions locally:**
```bash
# Install
# macOS: brew install act
# Windows: scoop install act
# Linux: See https://github.com/nektos/act

# List workflows
act -l

# Run a workflow
act -j test

# Run with specific event
act -e .github/workflows/event.json
```

---

## Git Tools

### Git Conventional Commits

**Status:** ✅ Recommended (already using)

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore

**Example:**
```
feat(evaluation): Add new scoring metric

Add support for weighted scoring across requirements.
Implement three-tier weighting system for critical/important/nice-to-have.

Closes #42
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

### Git Aliases

**Useful shortcuts to add to `.gitconfig`:**
```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --graph --oneline --all'
```

---

## Project-Specific Utilities

### Phoenix Integration

**Status:** Planned for Phase 1c

**Setup:**
1. Local Phoenix instance for development
2. Connection configuration in environment variables
3. Historical data storage for evaluations

**When to configure:**
- Issue #2 (Historical Score Tracking) work begins
- Dashboard development (Issue #3)

---

## Recommended Setup for Contributors

### Minimum Setup (Required)
```bash
# 1. Python 3.11+
python --version

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Dependencies
pip install -e ".[dev]"

# 4. Run tests
pytest

# Done! Ready to contribute
```

### Enhanced Setup (Recommended)
```bash
# All of the above, plus:

# 5. GitHub CLI (for issue/PR management)
# Install from: https://cli.github.com/

# 6. Code formatting
pip install black

# 7. Git aliases
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### Full Setup (Advanced)
```bash
# All of the above, plus:

# 8. Local testing tools
pip install pytest-watch

# 9. Jekyll for docs
gem install jekyll bundler

# 10. Additional linting
pip install flake8 mypy isort

# 11. Git enhanced features
brew install git-flow  # for release management

# Ready for advanced workflows!
```

---

## Decision Tree: Which Tool Do I Need?

```
Do you need to...?

├─ Create/manage issues via CLI?
│  └─ Yes → Use GitHub CLI (gh)
│
├─ Automate GitHub workflows in Python?
│  └─ Yes → Use PyGithub
│
├─ Format code consistently?
│  └─ Yes → pip install black
│
├─ Check code quality?
│  └─ Yes → pip install flake8 mypy
│
├─ Build documentation locally?
│  └─ Yes → gem install jekyll bundler
│
├─ Run GitHub Actions locally?
│  └─ Yes → brew install act
│
└─ Just code?
   └─ You're set! Use venv and pytest
```

---

## Setup Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created (`.venv/`)
- [ ] Dependencies installed (`pip install -e ".[dev]"`)
- [ ] Tests passing (`pytest`)
- [ ] Git configured with your name/email
- [ ] Git aliases configured (optional)
- [ ] GitHub CLI installed (optional, for issue management)
- [ ] Jekyll/Ruby installed (optional, for docs)

---

## Troubleshooting

### "Command not found: gh"
**Solution:** Install GitHub CLI from https://cli.github.com/

### "ModuleNotFoundError: No module named 'github'"
**Solution:** `pip install PyGithub` (not installed by default)

### "jekyll: command not found"
**Solution:** `gem install jekyll bundler` (requires Ruby)

### "act: command not found"
**Solution:** Install from https://github.com/nektos/act

---

## Resources

| Tool | Type | Documentation | When Added |
|------|------|---|---|
| GitHub CLI | Repo management | https://cli.github.com/manual | Phase 2+ |
| PyGithub | Python API | https://pygithub.readthedocs.io/ | Phase 2+ |
| Jekyll | Docs | https://jekyllrb.com/docs/ | ✅ Now |
| Black | Code formatting | https://black.readthedocs.io/ | Phase 2+ |
| Pytest | Testing | https://docs.pytest.org/ | ✅ Now |
| Pylance | Type checking | https://github.com/microsoft/pylance-release | ✅ Now |

---

## Contributing Guidelines

Before starting work:

1. ✅ Follow setup checklist above
2. ✅ Create feature branch: `git checkout -b feature/description`
3. ✅ Make changes following conventional commit style
4. ✅ Run tests: `pytest`
5. ✅ Format code: `black .` (if installed)
6. ✅ Commit with descriptive message
7. ✅ Push and create Pull Request
8. ✅ Link to corresponding GitHub issue

---

## Future Tool Additions

**When to add tools:**
- **GitHub CLI:** Phase 2 when issue automation starts
- **PyGithub:** Phase 2 when Python automation needed
- **Black/Flake8:** Anytime (useful for code quality)
- **act:** Anytime (useful for local CI/CD testing)

**How to add:**
1. Update `docs/DEVELOPER_TOOLS.md`
2. Add to `pyproject.toml` if Python package
3. Document installation and usage
4. Add to contributor setup checklist

---

## Questions or Suggestions?

- File an issue: https://github.com/CuriousPhysicist/evaluating-ai-agents-project-deeplearning-course/issues
- Reference: Link to this document
- Topic: "Enhancement: Add optional tool X"

---

**Last Updated:** 19 November 2026  
**Author:** Copilot  
**Purpose:** Guide for optional developer tools and utilities  
**Next Review:** Phase 2 (when automation tools are added)
