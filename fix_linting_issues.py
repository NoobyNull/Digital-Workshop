#!/usr/bin/env python
"""
Automatic Linting Issue Fixer for Candy-Cadence

Fixes common linting issues:
- Trailing whitespace
- Missing final newlines
- Unused imports
- Logging format issues

Usage:
    python fix_linting_issues.py              # Dry run
    python fix_linting_issues.py --apply      # Apply fixes
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"


class LintingFixer:
    """Fixes common linting issues."""
    
    def __init__(self, apply_changes: bool = False):
        self.apply_changes = apply_changes
        self.stats = {
            'trailing_whitespace': 0,
            'missing_final_newline': 0,
            'unused_imports': 0,
            'logging_format': 0,
            'files_processed': 0,
            'files_modified': 0,
        }
    
    def run(self) -> None:
        """Run all fixes."""
        print("\n" + "="*70)
        print("LINTING ISSUE FIXER")
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
            
            # Fix trailing whitespace
            content = self._fix_trailing_whitespace(content)
            
            # Fix missing final newline
            content = self._fix_missing_final_newline(content)
            
            # Fix logging format
            content = self._fix_logging_format(content)
            
            # Check if modified
            if content != original_content:
                self.stats['files_modified'] += 1
                
                if self.apply_changes:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✓ Fixed: {filepath.relative_to(PROJECT_ROOT)}")
                else:
                    print(f"⚠ Would fix: {filepath.relative_to(PROJECT_ROOT)}")
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            print(f"✗ Error processing {filepath}: {e}")
    
    def _fix_trailing_whitespace(self, content: str) -> str:
        """Remove trailing whitespace from lines."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.rstrip() != line:
                self.stats['trailing_whitespace'] += 1
            fixed_lines.append(line.rstrip())
        
        return '\n'.join(fixed_lines)
    
    def _fix_missing_final_newline(self, content: str) -> str:
        """Ensure file ends with newline."""
        if content and not content.endswith('\n'):
            self.stats['missing_final_newline'] += 1
            return content + '\n'
        return content
    
    def _fix_logging_format(self, content: str) -> str:
        """Convert old-style logging to lazy format."""
        # Pattern: logging.xxx("msg %s" % var)
        pattern = r'(logging\.\w+)\("([^"]*%[sd])"[^)]*%\s*([^)]+)\)'
        
        def replace_logging(match):
            self.stats['logging_format'] += 1
            func = match.group(1)
            msg = match.group(2)
            var = match.group(3)
            return f'{func}("{msg}", {var})'
        
        fixed = re.sub(pattern, replace_logging, content)
        return fixed
    
    def _print_summary(self) -> None:
        """Print summary of fixes."""
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files modified:  {self.stats['files_modified']}")
        print()
        print("Issues fixed:")
        print(f"  Trailing whitespace:    {self.stats['trailing_whitespace']}")
        print(f"  Missing final newline:  {self.stats['missing_final_newline']}")
        print(f"  Logging format:         {self.stats['logging_format']}")
        print()
        
        if self.apply_changes:
            print("✓ Changes applied!")
        else:
            print("⚠ Dry run - no changes applied")
            print("Run with --apply to apply fixes")
        
        print("="*70 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fix common linting issues"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply fixes (default is dry run)"
    )
    
    args = parser.parse_args()
    
    fixer = LintingFixer(apply_changes=args.apply)
    fixer.run()


if __name__ == "__main__":
    main()

