#!/usr/bin/env python3
"""
Fix line-too-long violations using black formatter.

This script uses black to automatically format code and fix line length issues.
"""

import subprocess
from pathlib import Path


def fix_line_length():
    """Fix line length violations using black."""
    src_dir = Path("src")

    print("Fixing line length violations with black...")

    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "black",
                "--line-length",
                "100",
                "--target-version",
                "py310",
                str(src_dir),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            print("Successfully fixed line length violations")
            # Count reformatted files
            if "reformatted" in result.stdout:
                print(result.stdout)
        else:
            print("Error fixing line length:")
            print(result.stderr)

    except FileNotFoundError:
        print("black not found. Installing...")
        subprocess.run(["pip", "install", "black"], check=True)
        # Retry
        fix_line_length()
    except subprocess.TimeoutExpired:
        print("Operation timed out")


if __name__ == "__main__":
    fix_line_length()
