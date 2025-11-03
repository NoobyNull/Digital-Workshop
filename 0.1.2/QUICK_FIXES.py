#!/usr/bin/env python3
"""
Quick Code Quality Fixes Script

Automatically fixes common code quality issues:
- Trailing whitespace
- Missing newlines at end of files
- Unused imports
- Import ordering
- Docstring formatting
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List


def fix_trailing_whitespace(src_dir: Path = Path("src")) -> int:
    """Remove trailing whitespace from all Python files."""
    print("Fixing trailing whitespace...")
    fixed = 0
    
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            original = content
            
            # Remove trailing whitespace
            content = re.sub(r"[ \t]+\n", "\n", content)
            
            # Ensure file ends with newline
            if content and not content.endswith("\n"):
                content += "\n"
            
            if content != original:
                py_file.write_text(content, encoding="utf-8")
                fixed += 1
                print(f"  ✓ {py_file}")
        except Exception as e:
            print(f"  ✗ {py_file}: {e}")
    
    print(f"Fixed {fixed} files\n")
    return fixed


def run_black_formatter(src_dir: Path = Path("src")) -> bool:
    """Run black code formatter."""
    print("Running black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(src_dir), "--line-length=120"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Black formatting complete\n")
            return True
        else:
            print(f"✗ Black failed: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"✗ Black not available: {e}\n")
        return False


def run_isort(src_dir: Path = Path("src")) -> bool:
    """Run isort to organize imports."""
    print("Running isort...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", str(src_dir), "--profile", "black", "--line-length", "120"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Import sorting complete\n")
            return True
        else:
            print(f"✗ isort failed: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"✗ isort not available: {e}\n")
        return False


def run_autoflake(src_dir: Path = Path("src")) -> bool:
    """Remove unused imports."""
    print("Removing unused imports...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "autoflake", "--remove-all-unused-imports", 
             "--in-place", "--recursive", str(src_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Unused imports removed\n")
            return True
        else:
            print(f"✗ autoflake failed: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"✗ autoflake not available: {e}\n")
        return False


def run_docformatter(src_dir: Path = Path("src")) -> bool:
    """Fix docstring formatting."""
    print("Fixing docstrings...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "docformatter", "--in-place", "--recursive", str(src_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Docstring formatting complete\n")
            return True
        else:
            print(f"✗ docformatter failed: {result.stderr}\n")
            return False
    except Exception as e:
        print(f"✗ docformatter not available: {e}\n")
        return False


def run_flake8_check(src_dir: Path = Path("src")) -> bool:
    """Check code with flake8."""
    print("Running flake8 check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(src_dir), "--max-line-length=120", "--exit-zero"],
            capture_output=True,
            text=True
        )
        
        # Count issues
        issues = len([line for line in result.stdout.split("\n") if line.strip()])
        print(f"✓ Found {issues} issues\n")
        return True
    except Exception as e:
        print(f"✗ flake8 not available: {e}\n")
        return False


def run_tests() -> bool:
    """Run test suite."""
    print("Running tests...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Extract summary
        lines = result.stdout.split("\n")
        for line in lines[-10:]:
            if line.strip():
                print(f"  {line}")
        
        print()
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Tests failed: {e}\n")
        return False


def main():
    """Run all quick fixes."""
    print("=" * 80)
    print("CODE QUALITY QUICK FIXES")
    print("=" * 80)
    print()
    
    src_dir = Path("src")
    if not src_dir.exists():
        print("Error: src directory not found")
        return 1
    
    # Run fixes
    fix_trailing_whitespace(src_dir)
    run_black_formatter(src_dir)
    run_isort(src_dir)
    run_autoflake(src_dir)
    run_docformatter(src_dir)
    run_flake8_check(src_dir)
    
    # Run tests
    print("=" * 80)
    print("RUNNING TESTS")
    print("=" * 80)
    print()
    
    if run_tests():
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

