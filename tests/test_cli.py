"""Basic tests for PowerLoom Snapshotter CLI"""

from snapshotter_cli import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"