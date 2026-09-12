<!-- markdownlint-configure-file {
  "MD043": {
    "headings": [
      "# Contributor Guide for AI Assistants",
      "## Repository map",
      "## Working agreement",
      "## Required local checks",
      "## Checks required by the changed area",
      "## CI expectations"
    ]
  }
} -->

# Contributor Guide for AI Assistants

This file is the short operational entry point for contributors using an AI
assistant. The same quality bar applies to assisted and unassisted changes.
Read the [contribution workflow](docs/source/contributing/workflow.md) for the
full setup instructions and the
[internals guide](docs/source/contributing/internals.md) before changing an
unfamiliar subsystem.

## Repository map

- `manim_slides/` contains the Python package and CLI implementation.
- `tests/` contains the pytest suite.
- `docs/source/` contains the Sphinx documentation.
- `.github/workflows/tests.yml` defines the cross-platform test matrix.
- `.pre-commit-config.yaml` is the source of truth for formatting, linting,
  type checking, spelling, and repository consistency checks.

## Working agreement

1. Start from a current `main` branch and keep the change scoped to one issue.
2. Inspect the existing implementation and tests before editing. Preserve both
   Manim Community and ManimGL behavior when the changed surface is shared.
3. Use `uv` and the checked-in lockfile. Set up the development environment
   with `uv sync` after installing the system dependencies listed in the
   [installation guide](docs/source/installation.md).
4. During implementation, run the narrowest relevant test first. For example:

   ```bash
   uv run pytest tests/test_slide.py -k relevant_test_name
   ```

5. Before opening a pull request, review the complete diff and run the required
   local checks below. Report any check you could not run and why; do not imply
   that an unrun check passed.

## Required local checks

Run both commands from the repository root:

```bash
uv run pre-commit run --all-files
uv run pytest
```

A ready change has no failing pre-commit hook and no failing pytest test. The
pre-commit command runs Ruff lint and formatting, ty type checking, codespell,
file-format checks, and repository-specific consistency checks.

## Checks required by the changed area

- Documentation changes: build the docs with `cd docs && uv run make html`.
  The rendered entry point is `docs/build/html/index.html`; inspect the changed
  page and resolve Sphinx warnings caused by the change.
- Template changes: keep generated or synchronized templates aligned with the
  repository-specific pre-commit hooks.
- GUI changes: exercise the affected interaction locally when the environment
  supports it, in addition to the automated tests.

Targeted tests are useful for iteration, but they do not replace the full
pre-commit and pytest runs before a pull request.

## CI expectations

GitHub Actions runs pytest across Linux, macOS, and Windows on every supported
Python version, checks installation extras, validates Markdown links, and runs
CodeQL and prose checks in their dedicated workflows. Local success does not
guarantee every platform will pass, so address CI failures that are caused by
the change and avoid weakening a check to make a failure disappear.

Keep commits reviewable, add or update tests for behavior changes, update the
closest documentation when user-visible behavior changes, and explain the
validation performed in the pull request.
