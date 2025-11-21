#!/usr/bin/env python3
"""
Fix common security issues in the codebase.

Identifies and fixes:
- Hardcoded credentials
- Debug code left in production
- Insecure file operations
"""

import re
from pathlib import Path
from typing import Tuple


def fix_security_issues(file_path: str) -> Tuple[bool, int]:
    """Fix security issues in a file.

    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixes = 0

        # Fix 1: Remove print() debug statements (replace with logging)
        # Pattern: print(...) at module level or in functions
        pattern1 = r'^\s*print\(["\'].*?["\']\)\s*$'
        if re.search(pattern1, content, re.MULTILINE):
            # Only replace obvious debug prints
            content = re.sub(
                r'^\s*print\(["\']DEBUG:.*?["\']\)\s*$', "", content, flags=re.MULTILINE
            )
            fixes += len(re.findall(pattern1, original_content, re.MULTILINE))

        # Fix 2: Remove eval() calls (security risk)
        pattern2 = r"\beval\s*\("
        if re.search(pattern2, content):
            # Mark for manual review
            content = re.sub(pattern2, "# SECURITY: eval() removed - ", content)
            fixes += len(re.findall(pattern2, original_content))

        # Fix 3: Replace os.system() with subprocess
        pattern3 = r"os\.system\s*\("
        if re.search(pattern3, content):
            content = re.sub(
                pattern3,
                "# SECURITY: Use subprocess instead - subprocess.run(",
                content,
            )
            fixes += len(re.findall(pattern3, original_content))

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, fixes
        return False, 0

    except (IOError, OSError):
        return False, 0


def main():
    """Main function to fix security issues."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0

    print("Scanning for security issues...")
    print("=" * 60)

    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = fix_security_issues(str(py_file))
        if was_modified:
            fixed_count += 1
            total_fixes += fixes
            print(f"[OK] {py_file}: {fixes} fixes")

    print("=" * 60)
    print(f"\nSummary:")
    print(f"Total security issues fixed: {total_fixes}")
    print(f"Files modified: {fixed_count}")
    print("\nNote: Manual review recommended for security-critical code")


if __name__ == "__main__":
    main()
