#!/usr/bin/env python3
"""
Test script to verify background and material thumbnail images are loading correctly.
"""

from pathlib import Path
from PIL import Image

def test_background_images():
    """Test that all background images exist and are valid."""
    print("=" * 60)
    print("Testing Background Images")
    print("=" * 60)
    
    bg_dir = Path("src/resources/backgrounds")
    if not bg_dir.exists():
        print(f"❌ Background directory not found: {bg_dir}")
        return False
    
    bg_files = list(bg_dir.glob("*.png"))
    if not bg_files:
        print(f"❌ No background images found in {bg_dir}")
        return False
    
    print(f"✓ Found {len(bg_files)} background images:")
    all_valid = True
    
    for bg_file in sorted(bg_files):
        try:
            img = Image.open(bg_file)
            print(f"  ✓ {bg_file.stem:20} - {img.size[0]}x{img.size[1]} ({img.format})")
        except Exception as e:
            print(f"  ❌ {bg_file.stem:20} - Error: {e}")
            all_valid = False
    
    return all_valid

def test_material_images():
    """Test that all material texture images exist and are valid."""
    print("\n" + "=" * 60)
    print("Testing Material Texture Images")
    print("=" * 60)
    
    mat_dir = Path("src/resources/materials")
    if not mat_dir.exists():
        print(f"❌ Material directory not found: {mat_dir}")
        return False
    
    # Get all .mtl files
    mtl_files = list(mat_dir.glob("*.mtl"))
    if not mtl_files:
        print(f"❌ No material files found in {mat_dir}")
        return False
    
    print(f"✓ Found {len(mtl_files)} material definitions:")
    all_valid = True
    
    for mtl_file in sorted(mtl_files):
        material_name = mtl_file.stem
        png_file = mat_dir / f"{material_name}.png"
        
        if png_file.exists():
            try:
                img = Image.open(png_file)
                print(f"  ✓ {material_name:20} - {img.size[0]}x{img.size[1]} ({img.format})")
            except Exception as e:
                print(f"  ❌ {material_name:20} - Error: {e}")
                all_valid = False
        else:
            print(f"  ⚠ {material_name:20} - No texture image found")
    
    return all_valid

def test_preferences_loading():
    """Test that preferences can load the thumbnail settings."""
    print("\n" + "=" * 60)
    print("Testing Preferences Loading")
    print("=" * 60)
    
    try:
        from src.core.application_config import ApplicationConfig
        config = ApplicationConfig.get_default()
        
        print(f"✓ ApplicationConfig loaded successfully")
        print(f"  - thumbnail_bg_image: {config.thumbnail_bg_image}")
        print(f"  - thumbnail_material: {config.thumbnail_material}")
        print(f"  - thumbnail_bg_color: {config.thumbnail_bg_color}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load ApplicationConfig: {e}")
        return False

if __name__ == "__main__":
    print("\n🔍 Thumbnail Preview System Test\n")
    
    results = {
        "Background Images": test_background_images(),
        "Material Images": test_material_images(),
        "Preferences Loading": test_preferences_loading(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("✓ All tests passed!" if all_passed else "❌ Some tests failed"))
    exit(0 if all_passed else 1)

