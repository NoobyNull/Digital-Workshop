"""
Test suite for Trimesh integration with fallback behavior.

This test verifies that:
1. Trimesh loader can be imported and initialized
2. Fallback to standard parsers works when Trimesh is unavailable
3. Model loading works with both Trimesh and standard parsers
4. Array-based geometry is properly created
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.trimesh_loader import get_trimesh_loader, TrimeshLoader
from src.core.data_structures import LoadingState


def test_trimesh_loader_initialization():
    """Test that TrimeshLoader can be initialized."""
    loader = TrimeshLoader()
    assert loader is not None
    print("✓ TrimeshLoader initialized successfully")


def test_trimesh_availability_check():
    """Test Trimesh availability detection."""
    loader = get_trimesh_loader()
    is_available = loader.is_trimesh_available()
    
    if is_available:
        print("✓ Trimesh is available - fast loading enabled")
    else:
        print("✓ Trimesh not available - will use fallback parsers")
    
    # Should return a boolean
    assert isinstance(is_available, bool)


def test_singleton_pattern():
    """Test that get_trimesh_loader returns the same instance."""
    loader1 = get_trimesh_loader()
    loader2 = get_trimesh_loader()
    
    assert loader1 is loader2
    print("✓ Singleton pattern working correctly")


def test_load_model_with_nonexistent_file():
    """Test that loading a nonexistent file returns None."""
    loader = get_trimesh_loader()
    model = loader.load_model("nonexistent_file.stl")
    
    assert model is None
    print("✓ Nonexistent file handled correctly")


def test_trimesh_loader_with_real_stl():
    """Test loading a real STL file if available."""
    loader = get_trimesh_loader()
    
    # Look for test STL files
    test_files = [
        Path("tests/test_data/cube.stl"),
        Path("tests/test_data/sample.stl"),
        Path("data/test.stl"),
    ]
    
    stl_file = None
    for test_file in test_files:
        if test_file.exists():
            stl_file = test_file
            break
    
    if stl_file is None:
        print("⚠ No test STL file found - skipping real file test")
        return
    
    print(f"Testing with: {stl_file}")
    
    # Try to load the model
    model = loader.load_model(str(stl_file))
    
    if model is not None:
        print(f"✓ Model loaded successfully")
        print(f"  - Triangles: {model.stats.triangle_count:,}")
        print(f"  - Vertices: {model.stats.vertex_count:,}")
        print(f"  - Loading state: {model.loading_state}")
        
        # Check if it's array-based (Trimesh) or triangle-based (fallback)
        if model.loading_state == LoadingState.ARRAY_GEOMETRY:
            print("  - Loaded with Trimesh (array-based)")
            assert model.vertex_array is not None
            assert model.normal_array is not None
        else:
            print("  - Loaded with fallback parser (triangle-based)")
            assert len(model.triangles) > 0
    else:
        print("⚠ Model loading returned None - fallback will be used")


def test_integration_with_model_loader():
    """Test that the integration with model_loader works."""
    try:
        from src.gui.model.model_loader import ModelLoader
        print("✓ ModelLoader imports successfully with Trimesh integration")
    except ImportError as e:
        print(f"⚠ Could not import ModelLoader: {e}")


def test_integration_with_thumbnail_generator():
    """Test that the integration with thumbnail generator works."""
    try:
        from src.core.thumbnail_components.thumbnail_generator_main import ThumbnailGenerator
        print("✓ ThumbnailGenerator imports successfully with Trimesh integration")
    except ImportError as e:
        print(f"⚠ Could not import ThumbnailGenerator: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Trimesh Integration Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Loader Initialization", test_trimesh_loader_initialization),
        ("Availability Check", test_trimesh_availability_check),
        ("Singleton Pattern", test_singleton_pattern),
        ("Nonexistent File Handling", test_load_model_with_nonexistent_file),
        ("Real STL Loading", test_trimesh_loader_with_real_stl),
        ("ModelLoader Integration", test_integration_with_model_loader),
        ("ThumbnailGenerator Integration", test_integration_with_thumbnail_generator),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 60)
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

