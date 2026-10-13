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

[doc('Apply automatic fixes (formatting and linting)')]
[group('Quality')]
fix: format
    ruff check --fix-only .
    statix fix .

[doc('Format code')]
[group('Quality')]
format:
    nix fmt

[doc('Run all static analysis checks')]
[group('Quality')]
check:
    ruff check .
    mypy
    vulture
    statix check .
    typos --config .typos.toml .
    nix flake check .  # This will check formatting too

[doc('Run all tests')]
[group('Quality')]
test:
    pytest

[doc('Run full CI pipeline: check, test, build')]
[group('Quality')]
ci: check test build

# =============================================================================
# Build
# =============================================================================

[doc('Build the Nix package')]
[group('Build')]
build:
    nix build

# =============================================================================
# Maintenance
# =============================================================================

[confirm('This will delete all build artifacts and caches. Continue?')]
[doc('Clean build artifacts and caches')]
[group('Maintenance')]
clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache \
           .coverage coverage.xml htmlcov result
    find . -type d -name "__pycache__" -exec rm -rf {} +
