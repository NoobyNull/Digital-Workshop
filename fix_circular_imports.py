#!/usr/bin/env python3
"""
Fix circular import issues in 3D-MM application.

This script automatically fixes the circular import between 
parsers/base_parser.py and core/model_cache.py by modifying the imports
to use local imports instead of global imports.
"""

import os
import re
import sys
from pathlib import Path

def fix_base_parser():
    """Fix circular import in base_parser.py."""
    base_parser_path = Path("src/parsers/base_parser.py")
    
    if not base_parser_path.exists():
        print(f"Error: {base_parser_path} not found")
        return False
    
    print(f"Fixing circular imports in {base_parser_path}...")
    
    # Read the file
    with open(base_parser_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the import exists
    if "from core.model_cache import get_model_cache, CacheLevel" not in content:
        print("No circular import found in base_parser.py")
        return True
    
    # Remove the global import
    content = re.sub(
        r"from core\.model_cache import get_model_cache, CacheLevel\n",
        "",
        content
    )
    
    # Add local imports in the __init__ method
    init_pattern = r"(def __init__\(self\):\s*\n\s*\"\"\"Initialize the parser\.\"\"\"\s*\n)"
    replacement = r"\1        # Local import to avoid circular dependency\n        from core.model_cache import get_model_cache, CacheLevel\n"
    content = re.sub(init_pattern, replacement, content)
    
    # Add local imports in other methods that need it
    methods_to_fix = [
        "parse_file",
        "parse_metadata_only",
        "_load_geometry_async"
    ]
    
    for method in methods_to_fix:
        pattern = f"(def {method}\\(self[^)]*\\):\\s*\n)"
        if "self.model_cache" in content and "from core.model_cache import" not in content.split(pattern)[1].split("def ")[0]:
            replacement = f"\\1        # Local import to avoid circular dependency\\n        from core.model_cache import get_model_cache, CacheLevel\\n"
            content = re.sub(pattern, replacement, content)
    
    # Write the file back
    with open(base_parser_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully fixed circular imports in {base_parser_path}")
    return True

def fix_main_py_imports():
    """Fix PySide5/PySide6 import inconsistency in main.py."""
    main_path = Path("src/main.py")
    
    if not main_path.exists():
        print(f"Error: {main_path} not found")
        return False
    
    print(f"Fixing import inconsistency in {main_path}...")
    
    # Read the file
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if PySide6 imports exist
    if "from PySide6" in content:
        # Replace PySide6 with PySide5
        content = content.replace("from PySide6", "from PySide5")
        
        # Write the file back
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully fixed PySide6 imports in {main_path}")
        return True
    else:
        print("No PySide6 imports found in main.py")
        return True

def main():
    """Main function to fix all circular imports."""
    print("3D-MM Circular Import Fix Tool")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("src").exists():
        print("Error: src directory not found. Please run this script from the project root.")
        sys.exit(1)
    
    success = True
    
    # Fix base_parser.py
    if not fix_base_parser():
        success = False
    
    # Fix main.py
    if not fix_main_py_imports():
        success = False
    
    print("=" * 40)
    if success:
        print("All circular import fixes applied successfully!")
        print("You can now run the application with: python src/main.py")
    else:
        print("Some fixes failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()