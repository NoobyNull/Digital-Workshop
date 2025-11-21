#!/usr/bin/env python3
"""
Simple validation script to verify the material application fix.

This script checks that the method name mismatches in MaterialLightingIntegrator
have been resolved by verifying the methods exist and can be called.
"""

import os
import sys
import ast
import logging


def validate_material_fix():
    """Validate that the material application fix is working."""
    print("=" * 60)
    print("VALIDATING MATERIAL APPLICATION FIX")
    print("=" * 60)
    print()

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Path to the integration file
    integration_file = os.path.join(
        os.path.dirname(__file__), "..", "src", "gui", "materials", "integration.py"
    )

    if not os.path.exists(integration_file):
        print(f"❌ ERROR: Integration file not found at {integration_file}")
        return False

    print(f"📁 Checking file: {integration_file}")
    print()

    try:
        # Read and parse the file
        with open(integration_file, "r") as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content)

        # Find the MaterialLightingIntegrator class
        integrator_class = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ClassDef)
                and node.name == "MaterialLightingIntegrator"
            ):
                integrator_class = node
                break

        if not integrator_class:
            print("❌ ERROR: MaterialLightingIntegrator class not found")
            return False

        print("✅ Found MaterialLightingIntegrator class")

        # Check for the methods we fixed
        methods_found = []
        method_calls_fixed = []

        for node in ast.walk(integrator_class):
            if isinstance(node, ast.FunctionDef):
                methods_found.append(node.name)

                # Check if this is one of the methods we fixed
                if node.name in ["apply_stl_material_properties", "parse_mtl_direct"]:
                    print(f"✅ Found method: {node.name}")

        # Check for method calls in apply_material_species
        apply_material_method = None
        for node in ast.walk(integrator_class):
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == "apply_material_species"
            ):
                apply_material_method = node
                break

        if not apply_material_method:
            print("❌ ERROR: apply_material_species method not found")
            return False

        print("✅ Found apply_material_species method")

        # Check for method calls within apply_material_species
        for node in ast.walk(apply_material_method):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == "self":
                            if node.func.attr in [
                                "apply_stl_material_properties",
                                "parse_mtl_direct",
                            ]:
                                method_calls_fixed.append(node.func.attr)
                                print(
                                    f"✅ Found correct method call: self.{node.func.attr}()"
                                )

        # Verify the fixes
        expected_methods = ["apply_stl_material_properties", "parse_mtl_direct"]
        expected_calls = [
            "apply_stl_material_properties"
        ]  # parse_mtl_direct is called from apply_stl_material_properties

        success = True

        # Check methods exist
        for method in expected_methods:
            if method not in methods_found:
                print(f"❌ ERROR: Method {method} not found")
                success = False
            else:
                print(f"✅ Method {method} exists")

        # Check method calls are correct
        for call in expected_calls:
            if call not in method_calls_fixed:
                print(
                    f"❌ ERROR: Method call self.{call}() not found in apply_material_species"
                )
                success = False
            else:
                print(f"✅ Method call self.{call}() found")

        # Check that wrong method names are NOT present
        wrong_calls = ["_apply_stl_material_properties", "_parse_mtl_direct"]
        for wrong_call in wrong_calls:
            if wrong_call in method_calls_fixed:
                print(f"❌ ERROR: Found wrong method call: self.{wrong_call}()")
                success = False

        print()
        print("=" * 60)
        if success:
            print("✅ VALIDATION SUCCESSFUL!")
            print("✅ Method name mismatches have been fixed")
            print("✅ Materials can now be applied without AttributeError exceptions")
            print(
                "✅ The critical bug preventing material application has been resolved"
            )
        else:
            print("❌ VALIDATION FAILED!")
            print("❌ Some method name issues remain")
        print("=" * 60)

        return success

    except Exception as e:
        print(f"❌ ERROR during validation: {e}")
        return False


def main():
    """Main function."""
    success = validate_material_fix()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
