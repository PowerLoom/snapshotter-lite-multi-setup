# Pre-commit Setup Instructions

This project uses pre-commit hooks to ensure code quality. Follow these steps to set it up:

## Quick Setup

```bash
# Install pre-commit hooks
uv run pre-commit install
```

## How It Works

1. **When you commit**: Pre-commit hooks automatically check your code
2. **If checks fail**: You'll see an error message with instructions
3. **To fix issues**: Run `./scripts/lint.sh fix`
4. **Commit again**: After fixing, your commit will succeed

## Commands

### Check code (no changes)
```bash
./scripts/lint.sh
```

### Fix code automatically
```bash
./scripts/lint.sh fix
```

### Skip checks for one commit (use sparingly)
```bash
git commit --no-verify
```

## What Gets Checked

- **Python formatting**: Black ensures consistent code style
- **Import sorting**: isort organizes imports
- **Whitespace**: No trailing spaces
- **File endings**: All files end with newline
- **YAML syntax**: Valid YAML files
- **File size**: Prevents large files (>1MB)
- **Merge conflicts**: No conflict markers

## Troubleshooting

If you see "command not found" errors:
```bash
uv sync
```

If hooks aren't running:
```bash
uv run pre-commit install --force
```
