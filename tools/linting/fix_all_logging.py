#!/usr/bin/env python3
"""
Fix all f-string logging violations by converting to % formatting.

This script handles complex cases with multiple variables and nested expressions.
"""

import re
from pathlib import Path
from typing import Tuple


def fix_fstring_logging(file_path: str) -> Tuple[bool, int]:
    """Fix f-string logging violations in a file.

    Converts logger.level(f"...{expr}...") to logger.level("...%s...", expr)

    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes = 0

        # Pattern to match logger calls with f-strings
        # Matches: logger.level(f"...{...}...")
        pattern = r'(logger\.(debug|info|warning|error|critical))\(f(["\'])([^"\']*?)\{([^}]+?)\}([^"\']*?)\3'

        def replace_func(match):
            nonlocal fixes
            logger_call = match.group(1)
            before = match.group(4)
            expr = match.group(5)
            after = match.group(6)
            quote = match.group(3)

            # Build the new format string
            new_format = f"{before}%s{after}"
            result = f"{logger_call}({quote}{new_format}{quote}, {expr}"
            fixes += 1
            return result

        # Replace all matches
        new_content = re.sub(pattern, replace_func, content)

        if new_content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, fixes
        return False, 0

    except (IOError, OSError):
        return False, 0


def main():
    """Main function to fix all logging violations."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0

    print("Fixing f-string logging violations...")
    print("=" * 60)

    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = fix_fstring_logging(str(py_file))
        if was_modified:
            fixed_count += 1
            total_fixes += fixes
            print(f"[OK] {py_file}: {fixes} fixes")

    print("=" * 60)
    print(f"\nSummary:")
    print(f"Total fixes applied: {total_fixes}")
    print(f"Files modified: {fixed_count}")


if __name__ == "__main__":
    main()
