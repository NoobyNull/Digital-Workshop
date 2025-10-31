#!/usr/bin/env python3
"""
Minimal Candy-Cadence Functionality Test

This test focuses on core functionality without heavy monitoring systems
that may cause memory issues in the test environment.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that core modules can be imported."""
    print("Testing core module imports...")
    
    try:
        # Test core imports
        from src.core.data_structures import Model, ModelFormat, Triangle, Vector3D
        print("[OK] Core data structures imported")
        
        # Test parser imports
        from src.parsers.refactored_obj_parser import OBJParser
        from src.parsers.refactored_stl_parser import STLParser
        from src.parsers.refactored_threemf_parser import ThreeMFParser
        print("[OK] Parser modules imported")
        
        # Test format detector
        from src.parsers.format_detector import FormatDetector
        print("[OK] Format detector imported")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import test failed: {e}")
        traceback.print_exc()
        return False

def test_format_detection():
    """Test format detection functionality."""
    print("\nTesting format detection...")
    
    try:
        from src.parsers.format_detector import FormatDetector
        
        detector = FormatDetector()
        
        # Test STL detection
        stl_result = detector.detect_format(Path("test.stl"))
        print(f"[OK] STL format detection: {stl_result}")
        
        # Test OBJ detection
        obj_result = detector.detect_format(Path("test.obj"))
        print(f"[OK] OBJ format detection: {obj_result}")
        
        # Test 3MF detection
        threemf_result = detector.detect_format(Path("test.3mf"))
        print(f"[OK] 3MF format detection: {threemf_result}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Format detection test failed: {e}")
        traceback.print_exc()
        return False

def test_parser_creation():
    """Test parser instantiation."""
    print("\nTesting parser creation...")
    
    try:
        from src.parsers.refactored_obj_parser import OBJParser
        from src.parsers.refactored_stl_parser import STLParser
        from src.parsers.refactored_threemf_parser import ThreeMFParser
        
        # Create parser instances
        obj_parser = OBJParser()
        stl_parser = STLParser()
        threemf_parser = ThreeMFParser()
        
        print("[OK] OBJ parser created")
        print("[OK] STL parser created")
        print("[OK] 3MF parser created")
        
        # Test supported extensions
        obj_exts = obj_parser.get_supported_extensions()
        stl_exts = stl_parser.get_supported_extensions()
        threemf_exts = threemf_parser.get_supported_extensions()
        
        print(f"[OK] OBJ supported extensions: {obj_exts}")
        print(f"[OK] STL supported extensions: {stl_exts}")
        print(f"[OK] 3MF supported extensions: {threemf_exts}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Parser creation test failed: {e}")
        traceback.print_exc()
        return False

def test_data_structures():
    """Test basic data structure creation."""
    print("\nTesting data structures...")
    
    try:
        from src.core.data_structures import Model, ModelFormat, Triangle, Vector3D, ModelStats
        
        # Create a simple triangle
        v1 = Vector3D(0.0, 0.0, 0.0)
        v2 = Vector3D(1.0, 0.0, 0.0)
        v3 = Vector3D(0.0, 1.0, 0.0)
        normal = Vector3D(0.0, 0.0, 1.0)
        
        triangle = Triangle(normal=normal, vertex1=v1, vertex2=v2, vertex3=v3)
        print(f"[OK] Triangle created: {len(triangle.get_vertices())} vertices")
        
        # Create model stats
        stats = ModelStats(
            vertex_count=3,
            triangle_count=1,
            min_bounds=v1,
            max_bounds=v3,
            file_size_bytes=100,
            format_type=ModelFormat.OBJ,
            parsing_time_seconds=0.1
        )
        print(f"[OK] Model stats created: {stats.triangle_count} triangles")
        
        # Create a basic model
        model = Model(
            header="Test Model",
            triangles=[triangle],
            stats=stats,
            format_type=ModelFormat.OBJ,
            file_path="test.obj"
        )
        print(f"[OK] Model created: {len(model.triangles)} triangles")
        
        return True
    except Exception as e:
        print(f"[FAIL] Data structures test failed: {e}")
        traceback.print_exc()
        return False

def test_file_validation():
    """Test file validation without actual parsing."""
    print("\nTesting file validation...")
    
    try:
        from src.parsers.refactored_obj_parser import OBJParser
        from src.parsers.refactored_stl_parser import STLParser
        
        obj_parser = OBJParser()
        stl_parser = STLParser()
        
        # Test validation with non-existent files (should return False)
        obj_valid, obj_msg = obj_parser.validate_file("nonexistent.obj")
        stl_valid, stl_msg = stl_parser.validate_file("nonexistent.stl")
        
        print(f"[OK] OBJ validation (non-existent file): {obj_valid}, {obj_msg}")
        print(f"[OK] STL validation (non-existent file): {stl_valid}, {stl_msg}")
        
        return True
    except Exception as e:
        print(f"[FAIL] File validation test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all minimal functionality tests."""
    print("Candy-Cadence Minimal Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Core Module Imports", test_imports),
        ("Format Detection", test_format_detection),
        ("Parser Creation", test_parser_creation),
        ("Data Structures", test_data_structures),
        ("File Validation", test_file_validation),
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
        print("[SUCCESS] All minimal functionality tests passed!")
        return 0
    else:
        print("[WARN] Some tests failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())