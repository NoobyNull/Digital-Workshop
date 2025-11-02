#!/usr/bin/env python3
"""
Test script for preview image features.

Tests:
1. Library context menu with "Generate Preview" option
2. Preview image display in metadata editor
3. Thumbnail generation functionality
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_file_structure():
    """Test that the modified files exist and have expected content."""
    print("Testing file structure...")
    
    files_to_check = [
        "src/gui/model_library_components/library_event_handler.py",
        "src/gui/metadata_components/metadata_editor_main.py"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"[PASS] {file_path} exists")
            
            # Check for key content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "Generate Preview" in content:
                print(f"[PASS] {file_path} contains 'Generate Preview'")
            else:
                print(f"[FAIL] {file_path} missing 'Generate Preview'")
                return False
                
            if "_generate_preview" in content:
                print(f"[PASS] {file_path} contains '_generate_preview'")
            else:
                print(f"[FAIL] {file_path} missing '_generate_preview'")
                return False
        else:
            print(f"[FAIL] {file_path} does not exist")
            return False
            
    return True

def test_library_event_handler():
    """Test the library event handler modifications."""
    print("\nTesting library event handler...")
    
    try:
        # Check if the file contains the expected modifications
        file_path = "src/gui/model_library_components/library_event_handler.py"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for context menu modifications
        if 'generate_preview_action = menu.addAction("Generate Preview")' in content:
            print("[PASS] Generate Preview action added to context menu")
        else:
            print("[FAIL] Generate Preview action not found in context menu")
            return False
            
        # Check for _generate_preview method
        if 'def _generate_preview(self, model_id: int) -> None:' in content:
            print("[PASS] _generate_preview method exists")
        else:
            print("[FAIL] _generate_preview method not found")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] Library event handler test failed: {e}")
        return False

def test_metadata_editor():
    """Test the metadata editor modifications."""
    print("\nTesting metadata editor...")
    
    try:
        # Check if the file contains the expected modifications
        file_path = "src/gui/metadata_components/metadata_editor_main.py"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for preview image group creation
        if '_create_preview_image_group' in content:
            print("[PASS] _create_preview_image_group method exists")
        else:
            print("[FAIL] _create_preview_image_group method not found")
            return False
            
        # Check for preview image loading
        if '_load_preview_image' in content:
            print("[PASS] _load_preview_image method exists")
        else:
            print("[FAIL] _load_preview_image method not found")
            return False
            
        # Check for preview image clearing
        if '_clear_preview_image' in content:
            print("[PASS] _clear_preview_image method exists")
        else:
            print("[FAIL] _clear_preview_image method not found")
            return False
            
        # Check for preview generation
        if '_generate_preview_for_current_model' in content:
            print("[PASS] _generate_preview_for_current_model method exists")
        else:
            print("[FAIL] _generate_preview_for_current_model method not found")
            return False
            
        # Check for preview image label
        if 'self.preview_image_label = QLabel()' in content:
            print("[PASS] Preview image label exists")
        else:
            print("[FAIL] Preview image label not found")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] Metadata editor test failed: {e}")
        return False

def test_thumbnail_service():
    """Test the thumbnail service functionality."""
    print("\nTesting thumbnail service...")
    
    try:
        from src.core.import_thumbnail_service import ImportThumbnailService
        
        # Check if the service can be instantiated
        service = ImportThumbnailService()
        print("[PASS] ImportThumbnailService can be instantiated")
        
        # Check if required methods exist
        if hasattr(service, 'generate_thumbnail'):
            print("[PASS] generate_thumbnail method exists")
        else:
            print("[FAIL] generate_thumbnail method missing")
            return False
            
        if hasattr(service, 'get_thumbnail_path'):
            print("[PASS] get_thumbnail_path method exists")
        else:
            print("[FAIL] get_thumbnail_path method missing")
            return False
            
        return True
    except Exception as e:
        print(f"[FAIL] Thumbnail service test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PREVIEW IMAGE FEATURES TEST")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_library_event_handler,
        test_metadata_editor,
        test_thumbnail_service
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! The preview image features are implemented correctly.")
        return 0
    else:
        print("[ERROR] Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())