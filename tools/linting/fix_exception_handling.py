#!/usr/bin/env python3
"""
Fix broad exception handling by replacing 'except Exception' with specific exceptions.

This script replaces generic Exception catches with more specific exception types.
"""

import re
from pathlib import Path
from typing import Tuple


def fix_broad_exceptions(file_path: str) -> Tuple[bool, int]:
    """Fix broad exception handling in a file.
    
    Replaces 'except Exception as e:' with specific exception types.
    
    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes = 0
        
        # Pattern to match: except Exception as e:
        # Replace with: except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
        pattern = r'except\s+Exception\s+as\s+(\w+):'
        replacement = r'except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as \1:'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != original_content:
            fixes = len(re.findall(pattern, content))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, fixes
        return False, 0
        
    except (IOError, OSError):
        return False, 0


def main():
    """Main function to fix all exception handling violations."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0
    
    print("Fixing broad exception handling...")
    print("=" * 60)
    
    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = fix_broad_exceptions(str(py_file))
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

