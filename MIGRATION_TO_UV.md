# Migration from Poetry to uv

This guide covers the migration from Poetry to uv for the Powerloom Snapshotter CLI project.

## What Changed

### Package Manager
- **Before**: Poetry for dependency management and packaging
- **After**: uv for faster, more efficient Python project management

### Key Files
- `pyproject.toml`: Updated to PEP 621 standard format (compatible with uv)
- `poetry.lock` → `uv.lock`: New lockfile format
- New scripts: `install-uv.sh` and `setup-uv.sh`

## For Developers

### Initial Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up development environment**:
   ```bash
   ./setup-uv.sh
   ```

### Common Commands

| Task | Poetry Command | uv Command |
|------|---------------|------------|
| Install dependencies | `poetry install` | `uv sync` |
| Add a dependency | `poetry add <package>` | `uv add <package>` |
| Add dev dependency | `poetry add --group dev <package>` | `uv add --dev <package>` |
| Run a command | `poetry run <command>` | `uv run <command>` |
| Build package | `poetry build` | `uv build` |
| Create venv | `poetry install` | `uv sync` |
| Update dependencies | `poetry update` | `uv lock --upgrade` |

### Development Workflow

```bash
# Install all dependencies
uv sync

# Run the CLI
uv run powerloom --help

# Run tests
uv run pytest

# Format code
./scripts/lint.sh fix

# Check code quality
./scripts/lint.sh

# Build binaries
PLATFORM=linux ARCH=x86_64 uv run pyinstaller pyinstaller.spec
```

## For End Users

### Installation

End users can install using the new installation script:
```bash
curl -sSL https://raw.githubusercontent.com/powerloom/snapshotter-lite-multi-setup/main/install-uv.sh | bash
```

Or install from PyPI when published:
```bash
uv tool install powerloom-snapshotter-cli
```

## CI/CD Changes

### GitHub Actions
All workflows have been updated to use uv:
- Uses `astral-sh/setup-uv@v5` action
- Caches based on `uv.lock` instead of `poetry.lock`
- Commands updated from `poetry run` to `uv run`

### Version Management
Version updates in `pyproject.toml` are now done directly via sed commands in CI, replacing `poetry version`.

## Benefits of uv

1. **Speed**: 10-100x faster than pip and poetry
2. **Simplicity**: Single tool for Python version management, virtual environments, and dependencies
3. **Compatibility**: Works with standard `pyproject.toml` (PEP 621)
4. **Built-in Python management**: No need for separate pyenv
5. **Better caching**: More efficient dependency resolution and caching

## Troubleshooting

### Virtual Environment Issues
If you see warnings about VIRTUAL_ENV not matching:
```bash
# Deactivate any active virtual environment
deactivate
# Use uv's environment
uv sync
```

### Python Version Issues
uv manages Python versions automatically:
```bash
# Pin to Python 3.12
uv python pin 3.12
# Install the pinned version
uv python install
```

### Missing Dependencies
If dependencies seem missing:
```bash
# Clean sync
rm -rf .venv
uv sync
```

## Notes for Maintainers

1. The `pyproject.toml` now uses PEP 621 format
2. Console scripts are defined in `[project.scripts]`
3. Dev dependencies are in `[tool.uv.dev-dependencies]`
4. Build system uses `hatchling` instead of `poetry-core`
5. The old Poetry-specific files (`poetry.lock`, Poetry sections in `pyproject.toml`) have been replaced
