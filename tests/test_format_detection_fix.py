#!/usr/bin/env python3
"""
Test to verify format detection fix for STL vs OBJ issue.

This test specifically checks that:
1. STL files are correctly detected as STL format
2. OBJ files are correctly detected as OBJ format
3. The format detection logging works properly
"""

import sys
import tempfile
from pathlib import Path


def create_test_stl_file(file_path: Path) -> None:
    """Create a test STL file with proper STL content."""
    stl_content = """solid test_cube
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 0.0 1.0
      vertex 1.0 1.0 1.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 1.0 1.0
      vertex 0.0 1.0 1.0
    endloop
  endfacet
endsolid test_cube
"""
    with open(file_path, 'w') as f:
        f.write(stl_content)


def create_test_obj_file(file_path: Path) -> None:
    """Create a test OBJ file with proper OBJ content."""
    obj_content = """# Test OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
f 1 2 3
f 1 3 4
"""
    with open(file_path, 'w') as f:
        f.write(obj_content)


def test_format_detection():
    """Test the format detection fix."""
    print("=== Testing Format Detection Fix ===")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    try:
        from src.parsers.format_detector import FormatDetector
        from src.core.data_structures import ModelFormat
        
        detector = FormatDetector()
        
        # Test with temporary STL file
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as stl_temp:
            stl_path = Path(stl_temp.name)
            create_test_stl_file(stl_path)
            
            print(f"Testing STL file: {stl_path.name}")
            stl_format = detector.detect_format(stl_path)
            print(f"Detected format: {stl_format}")
            
            if stl_format == ModelFormat.STL:
                print("✓ STL file correctly detected as STL")
                stl_result = True
            else:
                print(f"✗ STL file incorrectly detected as {stl_format}")
                stl_result = False
            
            stl_path.unlink()  # Clean up
        
        # Test with temporary OBJ file
        with tempfile.NamedTemporaryFile(suffix='.obj', delete=False) as obj_temp:
            obj_path = Path(obj_temp.name)
            create_test_obj_file(obj_path)
            
            print(f"\nTesting OBJ file: {obj_path.name}")
            obj_format = detector.detect_format(obj_path)
            print(f"Detected format: {obj_format}")
            
            if obj_format == ModelFormat.OBJ:
                print("✓ OBJ file correctly detected as OBJ")
                obj_result = True
            else:
                print(f"✗ OBJ file incorrectly detected as {obj_format}")
                obj_result = False
            
            obj_path.unlink()  # Clean up
        
        # Test OBJ verification method directly
        print(f"\nTesting OBJ verification method directly:")
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as stl_temp:
            stl_path = Path(stl_temp.name)
            create_test_stl_file(stl_path)
            
            obj_verification = detector._verify_obj_format(stl_path)
            print(f"STL file OBJ verification result: {obj_verification}")
            
            if not obj_verification:
                print("✓ STL file correctly rejected by OBJ verification")
                verification_result = True
            else:
                print("✗ STL file incorrectly accepted by OBJ verification")
                verification_result = False
            
            stl_path.unlink()  # Clean up
        
        # Summary
        print(f"\n=== Test Results ===")
        print(f"STL detection: {'PASS' if stl_result else 'FAIL'}")
        print(f"OBJ detection: {'PASS' if obj_result else 'FAIL'}")
        print(f"OBJ verification: {'PASS' if verification_result else 'FAIL'}")
        
        all_passed = stl_result and obj_result and verification_result
        print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
        
        if all_passed:
            print("\n✓ Format detection fix is working correctly!")
            print("STL files should no longer be detected as OBJ format.")
        else:
            print("\n✗ Format detection fix needs more work.")
        
        return all_passed
        
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the format detection test."""
    print("=== Format Detection Fix Test ===")
    print("Testing that STL files are correctly detected as STL, not OBJ\n")
    
    success = test_format_detection()
    
    if success:
        print("\n🎉 SUCCESS: Format detection issue has been resolved!")
        print("3D models should now get materials applied correctly.")
    else:
        print("\n❌ FAILURE: Format detection issue persists.")
        print("Further investigation needed.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)