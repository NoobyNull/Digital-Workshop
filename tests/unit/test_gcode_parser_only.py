#!/usr/bin/env python3
"""Test G-code parser only - no VTK or Qt required."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_parser_import():
    """Test that parser can be imported."""
    print("Testing GcodeParser import...")
    
    try:
        from src.gui.gcode_previewer_components.gcode_parser import GcodeParser, GcodeMove
        print("✓ GcodeParser imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parser_functionality():
    """Test GcodeParser functionality."""
    print("\nTesting GcodeParser functionality...")
    
    try:
        from src.gui.gcode_previewer_components.gcode_parser import GcodeParser
        
        parser = GcodeParser()
        print("✓ GcodeParser instantiated")
        
        # Test parsing simple G-code
        lines = [
            "G00 X10 Y20 Z5",
            "G01 X30 Y40 Z0 F100",
            "M06 T01",
            "M03 S1000",
            "G02 X50 Y50 I10 J10",
            "M05",
        ]
        
        moves = parser.parse_lines(lines)
        print(f"✓ Parsed {len(moves)} moves")
        
        # Verify move types
        for i, move in enumerate(moves):
            print(f"  Move {i}: {move.get_move_type_name()}")
        
        # Check statistics
        stats = parser.get_statistics()
        print(f"\n✓ Statistics:")
        print(f"  - Total moves: {stats['total_moves']}")
        print(f"  - Rapid moves: {stats['rapid_moves']}")
        print(f"  - Cutting moves: {stats['cutting_moves']}")
        print(f"  - Arc moves: {stats['arc_moves']}")
        print(f"  - Tool changes: {stats['tool_changes']}")
        
        return True
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("G-code Parser Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Parser Import", test_parser_import()))
    results.append(("Parser Functionality", test_parser_functionality()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ Parser tests passed!")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

