#!/usr/bin/env python3
"""
Test script to verify wallet address input handling.
Tests that lowercase 'b' characters are preserved in input.
"""

import os
import sys

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from snapshotter_cli.utils.console import Prompt


def test_wallet_input():
    """Test wallet address input with lowercase 'b' characters."""

    test_addresses = [
        "0x4A049eDd8348C17e9420dAef5EbA7007fEF0b62d",
        "0xbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbBbB",
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    ]

    print("Testing wallet address input handling...")
    print("This test verifies that lowercase 'b' characters are preserved.")
    print("-" * 60)

    for test_addr in test_addresses:
        print(f"\nTest address: {test_addr}")
        print("Please enter this exact address when prompted:")

        # Simulate the actual prompt used in configure.py
        user_input = Prompt.ask(
            "👉 Enter slot NFT holder wallet address (0x...)", default=""
        )

        if user_input == test_addr:
            print(f"✅ SUCCESS: Input preserved correctly!")
        else:
            print(f"❌ FAILURE: Input was modified!")
            print(f"   Expected: {test_addr}")
            print(f"   Got:      {user_input}")
            print(f"   Missing characters: {set(test_addr) - set(user_input)}")
            return False

    print("\n" + "=" * 60)
    print("✅ All tests passed! Wallet address input is working correctly.")
    return True


if __name__ == "__main__":
    # Test in both frozen and non-frozen environments
    if getattr(sys, "frozen", False):
        print("Running in PyInstaller frozen environment")
    else:
        print("Running in normal Python environment")

    print(f"Platform: {sys.platform}")
    print()

    success = test_wallet_input()
    sys.exit(0 if success else 1)
