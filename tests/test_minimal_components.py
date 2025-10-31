#!/usr/bin/env python3
"""
Minimal test to isolate component import issues.
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
    
    # Test 1: Database Manager
    try:
        print("1. Testing database_manager...")
        from src.core.database_manager import get_database_manager
        print("✓ Database manager import successful")
    except Exception as e:
        print(f"✗ Database manager import failed: {e}")
        return False
    
    # Test 2: Menu Manager
    try:
        print("2. Testing menu_manager...")
        from src.gui.components.menu_manager import MenuManager
        print("✓ Menu manager import successful")
    except Exception as e:
        print(f"✗ Menu manager import failed: {e}")
        return False
    
    # Test 3: Toolbar Manager  
    try:
        print("3. Testing toolbar_manager...")
        from src.gui.components.toolbar_manager import ToolbarManager
        print("✓ Toolbar manager import successful")
    except Exception as e:
        print(f"✗ Toolbar manager import failed: {e}")
        return False
    
    # Test 4: Status Bar Manager
    try:
        print("4. Testing status_bar_manager...")
        from src.gui.components.status_bar_manager import StatusBarManager
        print("✓ Status bar manager import successful")
    except Exception as e:
        print(f"✗ Status bar manager import failed: {e}")
        return False
    
    # Test 5: Dock Manager
    try:
        print("5. Testing dock_manager...")
        from src.gui.window.dock_manager import DockManager
        print("✓ Dock manager import successful")
    except Exception as e:
        print(f"✗ Dock manager import failed: {e}")
        return False
    
    # Test 6: Central Widget Manager
    try:
        print("6. Testing central_widget_manager...")
        from src.gui.window.central_widget_manager import CentralWidgetManager
        print("✓ Central widget manager import successful")
    except Exception as e:
        print(f"✗ Central widget manager import failed: {e}")
        return False
    
    # Test 7: Model Loader
    try:
        print("7. Testing model_loader...")
        from src.gui.model.model_loader import ModelLoader
        print("✓ Model loader import successful")
    except Exception as e:
        print(f"✗ Model loader import failed: {e}")
        return False
    
    # Test 8: Deduplication Service
    try:
        print("8. Testing deduplication_service...")
        from src.gui.services.deduplication_service import DeduplicationService
        print("✓ Deduplication service import successful")
    except Exception as e:
        print(f"✗ Deduplication service import failed: {e}")
        return False
    
    print("\nAll component imports successful!")
    return True

def test_main_window_init():
    """Test main window initialization steps."""
    print("\nTesting main window initialization...")
    
    try:
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        
        print("1. Creating main window instance...")
        from src.gui.main_window import MainWindow
        window = MainWindow()
        print("✓ Main window instance created")
        
        print("2. Testing window initialization...")
        # Don't call show() to avoid GUI issues in test
        window.hide()
        print("✓ Window initialization successful")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"✗ Main window initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Candy-Cadence Component Test")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed")
        sys.exit(1)
    
    # Test main window initialization
    if not test_main_window_init():
        print("\n❌ Main window tests failed")
        sys.exit(1)
    
    print("\n✅ All tests passed!")