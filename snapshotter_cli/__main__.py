#!/usr/bin/env python3
"""Entry point for PyInstaller builds."""

import sys
from snapshotter_cli.cli import app

def main():
    """Main entry point for the CLI."""
    return app()

if __name__ == "__main__":
    sys.exit(main())