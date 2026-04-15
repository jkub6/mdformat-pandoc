# Justfile for mdformat-pandoc
# Use 'just --list' to see available recipes

set shell := ["bash", "-c", "-u", "-o", "pipefail"]
set dotenv-load

[doc('List available recipes')]
default:
	@just --list

# =============================================================================
# Quality
# =============================================================================

[group('Quality')]
[doc('Apply automatic fixes (formatting and linting)')]
fix: format
  ruff check --fix-only .
  statix fix .

[group('Quality')]
[doc('Format code')]
format:
  nix fmt

[group('Quality')]
[doc('Run all static analysis checks')]
check:
	ruff check .
	mypy
	vulture
	statix check .
	typos --config .typos.toml .
	nix flake check --all-systems .  # This will check formatting too

[group('Quality')]
[doc('Run all tests')]
test:
	pytest

[group('Quality')]
[doc('Run full CI pipeline: check, test, build')]
ci: check test build

# =============================================================================
# Build
# =============================================================================

[group('Build')]
[doc('Build the Nix package')]
build:
	nix build

# =============================================================================
# Maintenance
# =============================================================================

[group('Maintenance')]
[doc('Clean build artifacts and caches')]
[confirm('This will delete all build artifacts and caches. Continue?')]
clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache \
	       .coverage coverage.xml htmlcov result
	find . -type d -name "__pycache__" -exec rm -rf {} +
