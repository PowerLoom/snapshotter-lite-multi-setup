#!/usr/bin/env python3
"""
Script to embed git commit hash into the package before building.
This is used during PyInstaller builds to include version info in binaries.
"""

import subprocess
import sys
from pathlib import Path


def get_git_commit():
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Could not get git commit: {e}", file=sys.stderr)
    return None


def embed_commit():
    """Embed the git commit into __init__.py."""
    # Find the __init__.py file
    init_file = Path(__file__).parent.parent / "snapshotter_cli" / "__init__.py"

    if not init_file.exists():
        print(f"Error: {init_file} not found", file=sys.stderr)
        return False

    commit = get_git_commit()
    if not commit:
        print("Warning: Could not get git commit, building without it", file=sys.stderr)
        return True

    # Read the file
    content = init_file.read_text()

    # Replace the __commit__ line
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("__commit__ = "):
            lines[i] = f'__commit__ = "{commit}"'
            break

    # Write back
    init_file.write_text("\n".join(lines))
    print(f"Embedded commit {commit} into {init_file}")
    return True


def restore_commit():
    """Restore __commit__ to None after build."""
    init_file = Path(__file__).parent.parent / "snapshotter_cli" / "__init__.py"

    if not init_file.exists():
        return

    content = init_file.read_text()
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("__commit__ = "):
            lines[i] = "__commit__ = None"
            break

    init_file.write_text("\n".join(lines))
    print(f"Restored __commit__ to None in {init_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        restore_commit()
    else:
        if not embed_commit():
            sys.exit(1)
