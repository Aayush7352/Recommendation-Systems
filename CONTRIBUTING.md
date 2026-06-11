# Contributing to RecSys Lab

We love contributions from everyone! This document outlines the process for contributing to this project, inspired by the development workflows used in major open-source projects like the Linux kernel.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Guidelines](#commit-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Security Issues](#security-issues)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Recommendation-Systems.git
   cd Recommendation-Systems
   ```
3. **Set up** the development environment:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -e "./backend[dev]"
   cd frontend && npm install && cd ..
   ```
4. **Create a branch** for your work:
   ```bash
   git checkout -b my-feature-branch
   ```

## Development Workflow

### Branch Naming Convention

Use descriptive branch names with a type prefix:

- `feat/` — New features (e.g., `feat/session-based-recommender`)
- `fix/` — Bug fixes (e.g., `fix/two-tower-nan-loss`)
- `docs/` — Documentation changes (e.g., `docs/api-reference`)
- `refactor/` — Code refactoring (e.g., `refactor/evaluation-pipeline`)
- `test/` — Adding or updating tests (e.g., `test/cold-start-coverage`)
- `chore/` — Maintenance tasks (e.g., `chore/update-dependencies`)

### Development Loop

1. Make your changes
2. Write or update tests
3. Run tests locally:
   ```bash
   .venv/bin/pytest backend/tests -v
   ```
4. Run linting:
   ```bash
   .venv/bin/ruff check backend/recsys backend/tests
   ```
5. Commit your changes (see [Commit Guidelines](#commit-guidelines))
6. Push to your fork and open a Pull Request

## Commit Guidelines

We follow a structured commit message format inspired by the Linux kernel and Conventional Commits:

### Format

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process or tooling changes |

### Examples

```
feat(models): add session-based GRU4Rec recommender

Implement a GRU-based session recommendation model with:
- Gated Recurrent Unit for sequence modeling
- Negative sampling for efficient training
- Top-K serving via cached item vectors

Closes #42
```

```
fix(api): handle missing timestamp column in user history

The /users/{id}/history endpoint crashed when the
interactions DataFrame had no timestamp column.

Fixes #87
```

## Code Style

### Python

- **Formatter**: We use [ruff](https://docs.astral.sh/ruff/) with the project configuration in `pyproject.toml`
- **Line length**: 100 characters
- **Type hints**: Required for all function signatures
- **Imports**: Grouped as: standard library → third-party → local; sorted alphabetically
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants

Run linting before committing:
```bash
.venv/bin/ruff check backend/recsys backend/tests
.venv/bin/ruff format --check backend/recsys backend/tests
```

### TypeScript / JavaScript

- **Formatter**: ESLint with the project configuration
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components

Run linting before committing:
```bash
cd frontend && npm run lint
```

## Testing

- All new features must include tests
- Bug fixes must include a regression test
- Tests are written with `pytest` for Python and `jest` for frontend

```bash
# Run all backend tests
.venv/bin/pytest backend/tests -v

# Run specific test
.venv/bin/pytest backend/tests/test_models.py -v -k "test_exclude_seen"

# Run with coverage
.venv/bin/pytest backend/tests --cov=recsys --cov-report=term
```

## Pull Request Process

1. **Ensure all tests pass** — CI will run automatically
2. **Update documentation** if you're adding or changing features
3. **Write a clear PR description** explaining what and why
4. **Link related issues** using GitHub keywords (Closes #42, Fixes #87)
5. **Request review** from maintainers
6. **Address review feedback** — discuss, push changes, resolve conversations
7. **Squash commits** if requested before merge

### PR Title Format

Same as commit messages: `<type>(<scope>): <summary>`

### PR Description Template

```markdown
## Summary
Brief description of the changes.

## Related Issues
Closes #...

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## Issue Reporting

### Bug Reports

When filing a bug report, please include:

- **Description**: Clear and concise description of the bug
- **Steps to reproduce**: Minimal, reproducible steps
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, dependency versions
- **Logs**: Relevant error messages or stack traces
- **Screenshots**: If applicable

### Feature Requests

When suggesting a new feature, please include:

- **Problem**: What problem does this solve?
- **Solution**: What would you like to see implemented?
- **Alternatives**: Any alternative solutions considered
- **Context**: Any additional context or references

## Security Issues

**Do not open public issues for security vulnerabilities.** Please follow our [Security Policy](SECURITY.md) for responsible disclosure.

## Review Process

Maintainers will review your PR and may request changes. This is normal! Here's what we look for:

- Correctness — does the code do what it claims?
- Test coverage — are there adequate tests?
- Performance — will this scale?
- Maintainability — is the code clean and well-structured?
- Documentation — are changes properly documented?

## Getting Help

- Open a [Discussion](https://github.com/Aayush7352/Recommendation-Systems/discussions)
- Join our community chat (coming soon)

---

Thank you for contributing to RecSys Lab! 🚀
