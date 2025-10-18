#!/usr/bin/env python
"""
Fix logging format issues - Phase 2

Converts old-style logging to lazy format:
- logging.info("msg %s" % var) -> logging.info("msg %s", var)
- logging.debug("msg %d" % num) -> logging.debug("msg %d", num)

Usage:
    python fix_logging_format.py              # Dry run
    python fix_logging_format.py --apply      # Apply fixes
"""

import sys
import re
from pathlib import Path
from typing import Tuple

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"


class LoggingFormatFixer:
    """Fixes logging format issues."""

    def __init__(self, apply_changes: bool = False):
        self.apply_changes = apply_changes
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'logging_fixes': 0,
        }

    def run(self) -> None:
        """Run all fixes."""
        print("\n" + "="*70)
        print("LOGGING FORMAT FIXER - PHASE 2")
        print("="*70)
        print(f"Mode: {'APPLY' if self.apply_changes else 'DRY RUN'}")
        print(f"Source: {SRC_DIR}")
        print("="*70 + "\n")

        # Find all Python files
        py_files = list(SRC_DIR.rglob("*.py"))
        print(f"Found {len(py_files)} Python files\n")

        for py_file in py_files:
            self._process_file(py_file)

        self._print_summary()

    def _process_file(self, filepath: Path) -> None:
        """Process a single file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix logging format
            content = self._fix_logging_format(content)

            # Check if modified
            if content != original_content:
                self.stats['files_modified'] += 1

                if self.apply_changes:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"[FIXED] {filepath.relative_to(PROJECT_ROOT)}")
                else:
                    print(f"[WOULD FIX] {filepath.relative_to(PROJECT_ROOT)}")

            self.stats['files_processed'] += 1

        except Exception as e:
            print(f"[ERROR] {filepath}: {e}")

    def _fix_logging_format(self, content: str) -> str:
        """Convert old-style logging to lazy format."""
        # Pattern: logging.xxx("msg %s" % var) or logging.xxx('msg %s' % var)
        # Matches: logging.info, logging.debug, logging.warning, logging.error, etc.

        patterns = [
            # Double quotes: logging.info("msg %s" % var)
            (
                r'(logging\.\w+)\("([^"]*%[sdiuoxXeEfFgGcr])"\s*%\s*([^)]+)\)',
                r'\1("\2", \3)'
            ),
            # Single quotes: logging.info('msg %s' % var)
            (
                r"(logging\.\w+)\('([^']*%[sdiuoxXeEfFgGcr])'\s*%\s*([^)]+)\)",
                r"\1('\2', \3)"
            ),
        ]

        for pattern, replacement in patterns:
            matches = re.findall(pattern, content)
            if matches:
                self.stats['logging_fixes'] += len(matches)
                content = re.sub(pattern, replacement, content)

        return content

    def _print_summary(self) -> None:
        """Print summary of fixes."""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files modified:  {self.stats['files_modified']}")
        print(f"Logging fixes:   {self.stats['logging_fixes']}")
        print()

        if self.apply_changes:
            print("[SUCCESS] Changes applied!")
        else:
            print("[INFO] Dry run - no changes applied")
            print("[INFO] Run with --apply to apply fixes")

        print("="*70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix logging format issues"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes (default is dry run)"
    )

    args = parser.parse_args()

    fixer = LoggingFormatFixer(apply_changes=args.apply)
    fixer.run()


if __name__ == "__main__":
    main()

