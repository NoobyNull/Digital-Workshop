#!/usr/bin/env python3
"""
Safely fix f-string logging violations by converting to % formatting.

This script is more conservative and only fixes simple, single-variable cases.
"""

import re
from pathlib import Path
from typing import Tuple


def fix_fstring_logging_safe(file_path: str) -> Tuple[bool, int]:
    """Safely fix f-string logging violations in a file.
    
    Only handles simple cases to avoid syntax errors.
    
    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        fixes = 0
        
        for i, line in enumerate(lines):
            # Only match simple patterns: logger.level(f"text {var}")
            # where var is a simple identifier or attribute access
            
            # Pattern: logger.level(f"...{simple_var}...")
            pattern = r'(logger\.(debug|info|warning|error|critical)\(f["\'])([^"\']*)\{([a-zA-Z_][a-zA-Z0-9_\.]*)\}([^"\']*)["\']'
            
            if re.search(pattern, line):
                def replace_func(m):
                    prefix = m.group(1)
                    before = m.group(3)
                    var = m.group(4)
                    after = m.group(5)
                    return '%s"%s%%s%s", %s' % (prefix, before, after, var)
                
                new_line = re.sub(pattern, replace_func, line)
                if new_line != line:
                    lines[i] = new_line
                    fixes += 1
        
        if lines != original_lines:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True, fixes
        return False, 0
    except (IOError, OSError):
        return False, 0


def main():
    """Main function to fix all logging violations."""
    src_dir = Path("src")
    fixed_count = 0
    total_fixes = 0
    
    print("Scanning for f-string logging violations (safe mode)...")
    
    for py_file in sorted(src_dir.rglob("*.py")):
        was_modified, fixes = fix_fstring_logging_safe(str(py_file))
        if was_modified:
            fixed_count += 1
            total_fixes += fixes
            print("[OK] %s: %d fixes" % (py_file, fixes))
    
    print("\n\nSummary:")
    print("Total fixes applied: %d" % total_fixes)
    print("Files modified: %d" % fixed_count)


if __name__ == "__main__":
    main()

