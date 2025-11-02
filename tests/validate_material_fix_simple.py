#!/usr/bin/env python3
"""
Simple validation script for material application fixes.

This script tests:
1. Material system method name fixes
2. Material resources availability
3. Basic ModelLoader integration
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def setup_logging():
    """Setup logging for the validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_material_system_fixes():
    """Test that material system method name fixes are working."""
    logger = setup_logging()
    logger.info("=== Testing Material System Fixes ===")
    
    try:
        # Test MaterialLightingIntegrator method name fixes
        from gui.materials.integration import MaterialLightingIntegrator
        
        integrator = MaterialLightingIntegrator()
        
        # Test that methods exist with correct names (no underscore prefix)
        methods_to_test = [
            'apply_stl_material_properties',
            'parse_mtl_direct'
        ]
        
        all_methods_exist = True
        for method_name in methods_to_test:
            if hasattr(integrator, method_name):
                logger.info(f"✓ MaterialLightingIntegrator has method: {method_name}")
            else:
                logger.error(f"✗ MaterialLightingIntegrator missing method: {method_name}")
                all_methods_exist = False
        
        if all_methods_exist:
            logger.info("✓ Material system method names are correct")
            return True
        else:
            logger.error("✗ Material system has missing methods")
            return False
            
    except Exception as e:
        logger.error(f"✗ Material system test ERROR: {e}")
        return False

def test_material_resources():
    """Test that material resources are available."""
    logger = setup_logging()
    logger.info("=== Testing Material Resources ===")
    
    try:
        materials_dir = Path(__file__).parent.parent / "src" / "resources" / "materials"
        
        if not materials_dir.exists():
            logger.error(f"✗ Materials directory not found: {materials_dir}")
            return False
        
        # Find all .mtl files
        mtl_files = list(materials_dir.glob("*.mtl"))
        
        if not mtl_files:
            logger.error("✗ No .mtl files found in materials directory")
            return False
        
        logger.info(f"✓ Found {len(mtl_files)} material files:")
        for mtl_file in mtl_files:
            logger.info(f"  - {mtl_file.name}")
        
        # Check for corresponding .png files
        png_files = list(materials_dir.glob("*.png"))
        logger.info(f"✓ Found {len(png_files)} texture files")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Material resources test ERROR: {e}")
        return False

def test_model_loader_integration():
    """Test ModelLoader integration with automatic material application."""
    logger = setup_logging()
    logger.info("=== Testing ModelLoader Integration ===")
    
    try:
        # Import the ModelLoader
        from gui.model.model_loader import ModelLoader
        
        # Create a mock main window
        from unittest.mock import Mock
        mock_main_window = Mock()
        mock_main_window.material_manager = Mock()
        mock_main_window.material_manager.get_species_list.return_value = ["maple", "cherry", "oak"]
        mock_main_window._apply_material_species = Mock()
        
        # Create ModelLoader instance
        model_loader = ModelLoader(mock_main_window)
        
        # Test _apply_default_material_from_preferences method exists
        if hasattr(model_loader, '_apply_default_material_from_preferences'):
            logger.info("✓ ModelLoader has _apply_default_material_from_preferences method")
        else:
            logger.error("✗ ModelLoader missing _apply_default_material_from_preferences method")
            return False
        
        # Test the method can be called without errors
        try:
            model_loader._apply_default_material_from_preferences()
            logger.info("✓ _apply_default_material_from_preferences method executes without errors")
        except Exception as e:
            logger.error(f"✗ _apply_default_material_from_preferences method failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ModelLoader integration test ERROR: {e}")
        return False

def run_simple_tests():
    """Run simple validation tests."""
    logger = setup_logging()
    logger.info("=== SIMPLE MATERIAL APPLICATION VALIDATION ===")
    
    tests = [
        ("Material System Fixes", test_material_system_fixes),
        ("Material Resources", test_material_resources),
        ("ModelLoader Integration", test_model_loader_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ {test_name} test CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n=== VALIDATION SUMMARY ===")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Material application system is working.")
        logger.info("\nKey Features Validated:")
        logger.info("✓ Material system method names are correct")
        logger.info("✓ Material resources are available")
        logger.info("✓ ModelLoader has automatic material application method")
        return True
    else:
        logger.error(f"\n❌ {failed} TESTS FAILED! Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)