"""
Console utilities for consistent terminal handling across the CLI.
Fixes newline issues in PyInstaller Linux builds.
"""

import sys

from rich.console import Console as RichConsole


def get_console() -> RichConsole:
    """
    Get a properly configured Rich Console instance.

    For PyInstaller frozen builds, forces standard terminal mode
    to fix newline handling issues on Linux.
    """
    if getattr(sys, "frozen", False):
        # Force standard terminal for PyInstaller builds
        return RichConsole(force_terminal=True, legacy_windows=False)
    else:
        return RichConsole()


# Global console instance
console = get_console()
