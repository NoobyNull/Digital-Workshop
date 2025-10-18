#!/usr/bin/env python3
"""
Test script to debug MTL file application issues.

This script will:
1. Test MaterialProvider MTL file parsing
2. Test MaterialManager texture loading
3. Test material application to VTK actors
4. Provide detailed logging output
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.logging_config import get_logger
from core.material_provider import MaterialProvider
from gui.material_manager import MaterialManager
from core.database_manager import get_database_manager

# Set up logging to see all debug messages
import logging
logging.basicConfig(level=logging.DEBUG)

logger = get_logger(__name__)

def test_mtl_parsing():
    """Test MTL file parsing in MaterialProvider."""
    print("\n=== Testing MTL File Parsing ===")

    provider = MaterialProvider()

    # Test getting available materials
    materials = provider.get_available_materials()
    print(f"Found {len(materials)} materials:")
    for material in materials:
        print(f"  - {material['name']}: {material.get('texture_path', 'No texture')}")
        if material.get('mtl_path'):
            print(f"    MTL file: {material['mtl_path']}")

            # Test parsing individual MTL file
            properties = provider._parse_mtl_file(material['mtl_path'])
            print(f"    Properties: {properties}")

def test_material_manager():
    """Test MaterialManager MTL-based material loading and application."""
    print("\n=== Testing MaterialManager (MTL-only) ===")

    db_manager = get_database_manager()
    material_manager = MaterialManager(db_manager)

    # Test getting species list from MaterialProvider directly (MTL-only)
    mtl_materials = material_manager.material_provider.get_available_materials()
    mtl_names = [m['name'] for m in mtl_materials if m.get('texture_path') and m.get('mtl_path')]
    print(f"Available MTL-only species: {mtl_names}")

    # Test MTL material loading for each species
    for species_name in mtl_names[:3]:  # Test first 3 MTL species
        print(f"\nTesting MTL species: {species_name}")
        try:
            # This should now use MTL textures, not procedural generation
            texture = material_manager.generate_wood_texture(species_name, size=(256, 256))
            print(f"  Loaded MTL texture shape: {texture.shape}, dtype: {texture.dtype}")
        except Exception as e:
            print(f"  Failed to load MTL texture: {e}")

    # Show the difference between old and new approaches
    old_species = material_manager.get_species_list()  # Old combined method
    print(f"\nOld combined species list: {old_species}")
    print(f"New MTL-only species list: {mtl_names}")
    print(f"Filtered out {len(old_species) - len(mtl_names)} non-MTL species")

def test_texture_loading():
    """Test loading actual texture files."""
    print("\n=== Testing Texture Loading ===")

    provider = MaterialProvider()

    # Check if texture files exist
    materials_dir = Path(__file__).parent / "src" / "resources" / "materials"
    print(f"Materials directory: {materials_dir}")
    print(f"Directory exists: {materials_dir.exists()}")

    if materials_dir.exists():
        texture_files = list(materials_dir.glob("*.png"))
        print(f"Found {len(texture_files)} texture files:")
        for texture_file in texture_files:
            print(f"  - {texture_file.name}")

            # Test loading the texture
            try:
                from gui.material_manager import MaterialManager
                import numpy as np

                # Create a dummy material manager just to test texture loading
                db_manager = get_database_manager()
                material_manager = MaterialManager(db_manager)

                img = material_manager._load_texture_image(texture_file, (256, 256))
                print(f"    Loaded texture shape: {img.shape}, dtype: {img.dtype}")
            except Exception as e:
                print(f"    Failed to load texture: {e}")

def main():
    """Run all tests."""
    print("Starting MTL file debugging tests...")

    try:
        test_mtl_parsing()
        test_material_manager()
        test_texture_loading()

        print("\n=== Test Summary ===")
        print("Check the log output above for detailed information about:")
        print("- MTL file parsing and path resolution")
        print("- Material discovery and loading")
        print("- Texture generation and application")
        print("- Any errors or warnings that might indicate the source of the problem")

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()