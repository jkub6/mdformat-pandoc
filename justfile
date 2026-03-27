# Justfile for mdformat-pandoc
# Use 'just --list' to see available recipes

set shell := ["bash", "-c", "-u", "-o", "pipefail"]

# --- Default ---

# List available recipes
default:
    @just --list

# =============================================================================
# Quality
# =============================================================================

[group('Quality')]
[doc('Apply automatic fixes (formatting and linting)')]
fix:
  ruff format .
  ruff check --fix-only .

[group('Quality')]
[doc('Alias for fix')]
format: fix

[group('Quality')]
[doc('Run all static analysis checks')]
check:
  ruff format --check .
  ruff check .
  mypy .

[group('Quality')]
[doc('Alias for check')]
lint: check

[group('Quality')]
[doc('Run all tests')]
test:
  pytest

[group('Quality')]
[doc('Run full CI pipeline: check, test')]
ci: check test
