#!/usr/bin/env python3
"""
Simple test to isolate component import issues.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """Test each major component import individually."""
    print("Testing component imports...")
    
    tests = [
        ("Database Manager", "src.core.database_manager", "get_database_manager"),
        ("Menu Manager", "src.gui.components.menu_manager", "MenuManager"),
        ("Toolbar Manager", "src.gui.components.toolbar_manager", "ToolbarManager"),
        ("Status Bar Manager", "src.gui.components.status_bar_manager", "StatusBarManager"),
        ("Dock Manager", "src.gui.window.dock_manager", "DockManager"),
        ("Central Widget Manager", "src.gui.window.central_widget_manager", "CentralWidgetManager"),
        ("Model Loader", "src.gui.model.model_loader", "ModelLoader"),
    ]
    
    failed_tests = []
    
    for i, (name, module, import_item) in enumerate(tests, 1):
        try:
            print(f"{i}. Testing {name.lower()}...")
            exec(f"from {module} import {import_item}")
            print(f"SUCCESS: {name} import successful")
        except Exception as e:
            print(f"FAILED: {name} import failed: {e}")
            failed_tests.append(name)
            import traceback
            traceback.print_exc()
    
    if failed_tests:
        print(f"\nFailed imports: {', '.join(failed_tests)}")
        return False
    else:
        print("\nAll imports successful!")
        return True

if __name__ == "__main__":
    print("Candy-Cadence Component Import Test")
    print("=" * 50)
    
    if test_imports():
        print("\nAll component tests passed!")
    else:
        print("\nSome component tests failed!")
        sys.exit(1)