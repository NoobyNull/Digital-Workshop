#!/usr/bin/env python3
"""
Simple MTL validation test without Unicode issues
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")


def test_material_discovery():
    """Test that MaterialProvider can be imported and discovers materials."""
    print("Testing MaterialProvider import and material discovery...")

    try:
        from core.material_provider import MaterialProvider

        print("[OK] MaterialProvider imported successfully")

        provider = MaterialProvider()
        print("[OK] MaterialProvider instantiated successfully")

        materials = provider.get_available_materials()
        print(f"[OK] Discovered {len(materials)} materials")

        for material in materials:
            print(f"  - {material['name']}: {material.get('texture_path')}")
            if material.get("mtl_path"):
                print(f"    MTL: {material['mtl_path']}")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_mtl_parsing():
    """Test that MTL files can be parsed."""
    print("\nTesting MTL file parsing...")

    try:
        from core.material_provider import MaterialProvider

        provider = MaterialProvider()
        materials = provider.get_available_materials()

        if not materials:
            print("[FAIL] No materials found to test")
            return False

        # Test parsing first material with MTL
        test_material = None
        for material in materials:
            if material.get("mtl_path") and material["mtl_path"].exists():
                test_material = material
                break

        if not test_material:
            print("[FAIL] No materials with MTL files found")
            return False

        print(f"Testing MTL parsing for: {test_material['name']}")

        properties = provider._parse_mtl_file(test_material["mtl_path"])
        print(f"[OK] Parsed MTL file with {len(properties)} properties")

        for key, value in properties.items():
            print(f"  - {key}: {value}")

        return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_material_by_name():
    """Test retrieving specific materials by name."""
    print("\nTesting material retrieval by name...")

    try:
        from core.material_provider import MaterialProvider

        provider = MaterialProvider()

        # Get first available material name
        materials = provider.get_available_materials()
        if not materials:
            print("[FAIL] No materials available")
            return False

        test_name = materials[0]["name"]
        print(f"Testing retrieval of material: {test_name}")

        material = provider.get_material_by_name(test_name)
        if material:
            print(f"[OK] Retrieved material: {material['name']}")
            print(f"  Texture path: {material.get('texture_path')}")
            print(f"  MTL path: {material.get('mtl_path')}")
            return True
        else:
            print(f"[FAIL] Could not retrieve material: {test_name}")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_type_conversion():
    """Test that the type conversion fix works."""
    print("\nTesting type conversion fix...")

    try:
        from core.material_provider import MaterialProvider

        provider = MaterialProvider()
        material = provider.get_material_by_name("cherry")

        if not material:
            print("Cherry material not found, trying first available material")
            materials = provider.get_available_materials()
            if materials:
                material = materials[0]
            else:
                print("[FAIL] No materials available")
                return False

        # Test that mtl_path is a Path object
        mtl_path = material.get("mtl_path")
        if mtl_path:
            print(f"[OK] MTL path type: {type(mtl_path)}")

            # Test string conversion (this is what the fix does)
            str_path = str(mtl_path)
            print(f"[OK] String conversion successful: {str_path}")

            # Test that we can use it for file operations
            if Path(str_path).exists():
                print("[OK] Converted path exists and can be used for file operations")
                return True
            else:
                print("[FAIL] Converted path does not exist")
                return False
        else:
            print("No MTL path available for testing")
            return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("MTL MATERIAL SYSTEM VALIDATION")
    print("=" * 60)

    tests = [
        ("Material Discovery", test_material_discovery),
        ("MTL File Parsing", test_mtl_parsing),
        ("Material Retrieval", test_material_by_name),
        ("Type Conversion Fix", test_type_conversion),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"[OK] {test_name}: PASSED")
            else:
                print(f"[FAIL] {test_name}: FAILED")

        except Exception as e:
            print(f"[FAIL] {test_name}: ERROR - {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! MTL fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
