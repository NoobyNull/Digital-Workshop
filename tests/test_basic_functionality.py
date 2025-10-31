#!/usr/bin/env python3
"""
Basic Functionality Test for Candy-Cadence Application

Tests core functionality including:
- Model loading and parsing
- 3D viewer functionality
- Basic UI interactions
- Performance monitoring
"""

import sys
import time
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.gui.main_window import MainWindow
from src.parsers.stl_parser import STLParser
from src.parsers.obj_parser import OBJParser
from src.parsers.threemf_parser import ThreeMFParser
from src.core.data_structures import Model
from src.core.performance_monitor import get_performance_monitor

def test_model_loading():
    """Test loading various 3D model formats."""
    print("Testing model loading functionality...")
    
    # Test STL file
    stl_file = Path("tests/sample_files/cube_ascii.stl")
    if stl_file.exists():
        try:
            parser = STLParser()
            model = parser.parse_file(str(stl_file))
            print(f"[OK] STL file loaded successfully: {model.stats.triangle_count} triangles")
        except Exception as e:
            print(f"[FAIL] STL file loading failed: {e}")
            return False
    else:
        print("[WARN] STL test file not found")
    
    # Test OBJ file
    obj_file = Path("tests/sample_files/cube.obj")
    if obj_file.exists():
        try:
            parser = OBJParser()
            model = parser.parse_file(str(obj_file))
            print(f"[OK] OBJ file loaded successfully: {model.stats.triangle_count} triangles")
        except Exception as e:
            print(f"[FAIL] OBJ file loading failed: {e}")
            return False
    else:
        print("[WARN] OBJ test file not found")
    
    # Test 3MF file
    threemf_file = Path("tests/sample_files/cube.3mf")
    if threemf_file.exists():
        try:
            parser = ThreeMFParser()
            model = parser.parse_file(str(threemf_file))
            print(f"[OK] 3MF file loaded successfully: {model.stats.triangle_count} triangles")
        except Exception as e:
            print(f"[FAIL] 3MF file loading failed: {e}")
            return False
    else:
        print("[WARN] 3MF test file not found")
    
    return True

def test_performance_monitoring():
    """Test performance monitoring system."""
    print("\nTesting performance monitoring...")
    
    try:
        monitor = get_performance_monitor()
        report = monitor.get_performance_report()
        
        print(f"[OK] Performance monitor working")
        print(f"   - Current metrics: {len(report.get('current_metrics', {}))} metrics")
        print(f"   - System info: {report.get('system_info', {})}")
        print(f"   - Monitoring active: {report.get('monitoring_status', {}).get('active', False)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Performance monitoring failed: {e}")
        return False

def test_basic_ui_functionality():
    """Test basic UI functionality."""
    print("\nTesting basic UI functionality...")
    
    try:
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        print("[OK] Main window created successfully")
        
        # Test window visibility
        window.show()
        window.hide()
        print("[OK] Window show/hide functionality working")
        
        # Test viewer widget
        if hasattr(window, 'viewer_widget') and window.viewer_widget:
            print("[OK] 3D viewer widget available")
        else:
            print("[WARN] 3D viewer widget not found")
        
        # Clean up
        window.close()
        
        return True
    except Exception as e:
        print(f"[FAIL] UI functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_memory_management():
    """Test memory management functionality."""
    print("\nTesting memory management...")
    
    try:
        from src.core.memory_manager import get_memory_manager
        
        memory_manager = get_memory_manager()
        status = memory_manager.get_memory_status()
        
        print(f"[OK] Memory manager working")
        print(f"   - Process memory: {status.get('process_memory_mb', 0):.1f} MB")
        print(f"   - System memory: {status.get('system_memory_percent', 0):.1f}%")
        print(f"   - Memory limit: {status.get('memory_limit_mb', 0)} MB")
        
        return True
    except Exception as e:
        print(f"[FAIL] Memory management test failed: {e}")
        return False

def main():
    """Run all basic functionality tests."""
    print("Candy-Cadence Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Model Loading", test_model_loading),
        ("Performance Monitoring", test_performance_monitoring),
        ("Memory Management", test_memory_management),
        ("Basic UI Functionality", test_basic_ui_functionality),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All basic functionality tests passed!")
        return 0
    else:
        print("[WARN] Some tests failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())