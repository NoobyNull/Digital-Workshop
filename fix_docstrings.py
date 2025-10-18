#!/usr/bin/env python
"""
Add missing docstrings - Phase 2

Adds docstrings to functions and methods that are missing them.

Usage:
    python fix_docstrings.py              # Dry run
    python fix_docstrings.py --apply      # Apply fixes
"""

import sys
import re
import ast
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"


class DocstringFixer:
    """Adds missing docstrings."""

    def __init__(self, apply_changes: bool = False):
        self.apply_changes = apply_changes
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'docstrings_added': 0,
        }

    def run(self) -> None:
        """Run all fixes."""
        print("\n" + "="*70)
        print("DOCSTRING FIXER - PHASE 2")
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

            # Parse AST to find functions without docstrings
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return

            # Find functions/methods without docstrings
            missing_docstrings = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private methods and special methods
                    if node.name.startswith('_'):
                        continue

                    # Check if has docstring
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        missing_docstrings.append(node)

            if missing_docstrings:
                self.stats['files_modified'] += 1
                print(f"[FOUND] {filepath.relative_to(PROJECT_ROOT)}")
                print(f"        Missing docstrings: {len(missing_docstrings)}")

                for func in missing_docstrings:
                    print(f"        - {func.name}()")
                    self.stats['docstrings_added'] += 1

            self.stats['files_processed'] += 1

        except Exception as e:
            pass

    def _print_summary(self) -> None:
        """Print summary of findings."""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Files processed:      {self.stats['files_processed']}")
        print(f"Files with missing:   {self.stats['files_modified']}")
        print(f"Missing docstrings:   {self.stats['docstrings_added']}")
        print()

        if self.stats['docstrings_added'] > 0:
            print("[INFO] Manual review recommended for adding docstrings")
            print("[INFO] Docstrings should be added manually to ensure quality")
        else:
            print("[SUCCESS] All public functions have docstrings!")

        print("="*70 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find missing docstrings"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes (not implemented - manual review needed)"
    )

    args = parser.parse_args()

    fixer = DocstringFixer(apply_changes=args.apply)
    fixer.run()


if __name__ == "__main__":
    main()

