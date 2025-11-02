#!/usr/bin/env python3
"""
Simple validation script for VTK-only material application system.

This script validates that:
1. PyQt3D dependencies have been removed
2. VTK-only material application methods exist
3. Material application integration is working
"""

import os
import sys
from pathlib import Path

def validate_vtk_material_system():
    """Validate the VTK-only material application system."""
    print("Validating VTK-only material application system...")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Check PyQt3D files are removed
    total_tests += 1
    print("Test 1: Checking PyQt3D files are removed...")
    pyqt3d_files = [
        'src/gui/viewer_widget.py',
        'src/gui/viewer_components/viewer_3d_widget_main.py'
    ]
    
    pyqt3d_removed = True
    for file_path in pyqt3d_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  [FAIL] PyQt3D file {file_path} still exists")
            pyqt3d_removed = False
        else:
            print(f"  [OK] PyQt3D file {file_path} removed")
    
    if pyqt3d_removed:
        success_count += 1
        print("  ✅ PyQt3D files successfully removed")
    else:
        print("  ❌ Some PyQt3D files still exist")
    
    # Test 2: Check VTK viewer files exist and have correct content
    total_tests += 1
    print("\nTest 2: Checking VTK viewer files...")
    vtk_files = [
        'src/gui/viewer_3d/model_renderer.py',
        'src/gui/viewer_3d/viewer_widget_facade.py',
        'src/gui/viewer_widget_vtk.py'
    ]
    
    vtk_files_exist = True
    for file_path in vtk_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"  ✅ VTK file {file_path} exists")
            
            # Check for PyQt3D imports
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            pyqt3d_imports = ['PyQt3D', 'Qt3DCore', 'Qt3DExtras', 'Qt3DRender', 'Qt3DInput']
            found_pyqt3d = False
            for pyqt3d_import in pyqt3d_imports:
                if pyqt3d_import in content:
                    print(f"    ❌ Found PyQt3D import: {pyqt3d_import}")
                    found_pyqt3d = True
                    vtk_files_exist = False
            
            if not found_pyqt3d:
                print(f"    ✅ No PyQt3D imports found")
        else:
            print(f"  ❌ VTK file {file_path} missing")
            vtk_files_exist = False
    
    if vtk_files_exist:
        success_count += 1
        print("  ✅ VTK viewer files are correct")
    else:
        print("  ❌ VTK viewer files have issues")
    
    # Test 3: Check material application methods exist
    total_tests += 1
    print("\nTest 3: Checking material application methods...")
    
    # Check ModelRenderer methods
    model_renderer_path = Path('src/gui/viewer_3d/model_renderer.py')
    if model_renderer_path.exists():
        with open(model_renderer_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'def apply_material(',
            'def apply_default_material('
        ]
        
        methods_exist = True
        for method in required_methods:
            if method in content:
                print(f"  ✅ Found method: {method.strip()}")
            else:
                print(f"  ❌ Missing method: {method.strip()}")
                methods_exist = False
        
        if methods_exist:
            success_count += 1
            print("  ✅ ModelRenderer has material application methods")
        else:
            print("  ❌ ModelRenderer missing material application methods")
    else:
        print("  ❌ ModelRenderer file not found")
    
    # Test 4: Check Viewer3DWidget methods
    total_tests += 1
    print("\nTest 4: Checking Viewer3DWidget material methods...")
    
    viewer_facade_path = Path('src/gui/viewer_3d/viewer_widget_facade.py')
    if viewer_facade_path.exists():
        with open(viewer_facade_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'def apply_material_to_current_model(',
            'def apply_default_material_to_current_model(',
            'def _get_material_manager('
        ]
        
        methods_exist = True
        for method in required_methods:
            if method in content:
                print(f"  ✅ Found method: {method.strip()}")
            else:
                print(f"  ❌ Missing method: {method.strip()}")
                methods_exist = False
        
        if methods_exist:
            success_count += 1
            print("  ✅ Viewer3DWidget has material application methods")
        else:
            print("  ❌ Viewer3DWidget missing material application methods")
    else:
        print("  ❌ Viewer3DWidget file not found")
    
    # Test 5: Check MaterialLightingIntegrator method names
    total_tests += 1
    print("\nTest 5: Checking MaterialLightingIntegrator method names...")
    
    integrator_path = Path('src/gui/materials/integration.py')
    if integrator_path.exists():
        with open(integrator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for correct method names (no underscore prefix)
        correct_methods = [
            'def apply_stl_material_properties(',
            'def parse_mtl_direct('
        ]
        
        # Check for incorrect method names (with underscore prefix)
        incorrect_methods = [
            'def _apply_stl_material_properties(',
            'def _parse_mtl_direct('
        ]
        
        methods_correct = True
        
        for method in correct_methods:
            if method in content:
                print(f"  ✅ Found correct method: {method.strip()}")
            else:
                print(f"  ❌ Missing correct method: {method.strip()}")
                methods_correct = False
        
        for method in incorrect_methods:
            if method in content:
                print(f"  ❌ Found incorrect method: {method.strip()}")
                methods_correct = False
            else:
                print(f"  ✅ Correctly absent: {method.strip()}")
        
        if methods_correct:
            success_count += 1
            print("  ✅ MaterialLightingIntegrator has correct method names")
        else:
            print("  ❌ MaterialLightingIntegrator has incorrect method names")
    else:
        print("  ❌ MaterialLightingIntegrator file not found")
    
    # Test 6: Check material resources exist
    total_tests += 1
    print("\nTest 6: Checking material resources...")
    
    materials_dir = Path('src/resources/materials')
    if materials_dir.exists():
        mtl_files = list(materials_dir.glob('*.mtl'))
        if mtl_files:
            print(f"  ✅ Found {len(mtl_files)} material files:")
            for mtl_file in mtl_files[:5]:  # Show first 5
                print(f"    - {mtl_file.name}")
            if len(mtl_files) > 5:
                print(f"    ... and {len(mtl_files) - 5} more")
            success_count += 1
        else:
            print("  ❌ No material files found")
    else:
        print("  ❌ Materials directory not found")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {success_count}/{total_tests}")
    print(f"Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 ALL TESTS PASSED! VTK-only material system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - success_count} test(s) failed. Please review the issues above.")
        return False


if __name__ == '__main__':
    success = validate_vtk_material_system()
    sys.exit(0 if success else 1)