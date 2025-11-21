#!/usr/bin/env python3
"""
Add basic type hints to functions missing them.

This script adds type hints to function definitions that are missing them.
"""

import re
from pathlib import Path
from typing import Tuple


def add_type_hints(file_path: str) -> Tuple[bool, int]:
    """Add type hints to functions in a file.

    Adds basic type hints to function definitions.

    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_lines = lines.copy()
        fixes = 0

        for i, line in enumerate(lines):
            # Skip if line already has type hints or is not a function def
            if "->" in line or "def " not in line:
                continue

            # Pattern: def function_name(args):
            # Add -> None if no return type specified
            if re.search(r"def\s+\w+\([^)]*\):\s*$", line):
                # Add -> None before the colon
                new_line = re.sub(r"(\))\s*:", r"\1 -> None:", line)
                if new_line != line:
                    lines[i] = new_line
                    fixes += 1

        if lines != original_lines:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True, fixes
        return False, 0

    except (IOError, OSError):
        return False, 0


def main():
    """Main function to add type hints."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0

    print("Adding type hints to functions...")
    print("=" * 60)

    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = add_type_hints(str(py_file))
        if was_modified:
            fixed_count += 1
            total_fixes += fixes
            print(f"[OK] {py_file}: {fixes} fixes")

    print("=" * 60)
    print(f"\nSummary:")
    print(f"Total type hints added: {total_fixes}")
    print(f"Files modified: {fixed_count}")


if __name__ == "__main__":
    main()
