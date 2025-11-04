#!/usr/bin/env python3
"""
Remove unused imports using autoflake.

This script uses autoflake to automatically remove unused imports.
"""

import subprocess
from pathlib import Path


def remove_unused_imports():
    """Remove unused imports from all Python files."""
    src_dir = Path("src")
    
    print("Removing unused imports...")
    
    # Use autoflake to remove unused imports
    try:
        result = subprocess.run(
            [
                "python", "-m", "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--recursive",
                str(src_dir)
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("Successfully removed unused imports")
            if result.stdout:
                print(result.stdout)
        else:
            print("Error removing unused imports:")
            print(result.stderr)
            
    except FileNotFoundError:
        print("autoflake not found. Installing...")
        subprocess.run(["pip", "install", "autoflake"], check=True)
        # Retry
        remove_unused_imports()
    except subprocess.TimeoutExpired:
        print("Operation timed out")


if __name__ == "__main__":
    remove_unused_imports()

