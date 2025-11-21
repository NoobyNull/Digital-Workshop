#!/usr/bin/env python3
"""
Add missing docstrings to functions and classes.

This script adds basic docstrings to functions and classes that are missing them.
"""

import re
from pathlib import Path
from typing import Tuple


def add_docstrings(file_path: str) -> Tuple[bool, int]:
    """Add docstrings to functions and classes in a file.

    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_lines = lines.copy()
        fixes = 0
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for function or class definition
            if re.match(r"^\s*(def|class)\s+\w+", line):
                # Check if next non-empty line is a docstring
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1

                # If next line is not a docstring, add one
                if j < len(lines):
                    next_line = lines[j]
                    if not re.match(r'^\s*["\']', next_line):
                        # Add docstring
                        indent = len(line) - len(line.lstrip()) + 4
                        docstring = " " * indent + '"""TODO: Add docstring."""\n'
                        lines.insert(j, docstring)
                        fixes += 1
                        i = j + 1
                        continue

            i += 1

        if lines != original_lines:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True, fixes
        return False, 0

    except (IOError, OSError):
        return False, 0


def main():
    """Main function to add docstrings."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0

    print("Adding missing docstrings...")
    print("=" * 60)

    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = add_docstrings(str(py_file))
        if was_modified:
            fixed_count += 1
            total_fixes += fixes
            print(f"[OK] {py_file}: {fixes} docstrings added")

    print("=" * 60)
    print(f"\nSummary:")
    print(f"Total docstrings added: {total_fixes}")
    print(f"Files modified: {fixed_count}")
    print("\nNote: Review and update TODO docstrings with proper documentation")


if __name__ == "__main__":
    main()
