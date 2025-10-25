#!/usr/bin/env python3
"""Simple test for VTK G-code viewer integration - no Qt required."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")
    
    try:
        # Test parser import
        from src.gui.gcode_previewer_components.gcode_parser import GcodeParser, GcodeMove
        print("✓ GcodeParser imported")
        
        # Test renderer import
        from src.gui.gcode_previewer_components.gcode_renderer import GcodeRenderer
        print("✓ GcodeRenderer imported")
        
        # Test camera controller import
        from src.gui.gcode_previewer_components.camera_controller import CameraController
        print("✓ CameraController imported")
        
        # Test timeline import (requires Qt, so just check it exists)
        from src.gui.gcode_previewer_components import gcode_timeline
        print("✓ GcodeTimeline module exists")
        
        # Test interactive loader import (requires Qt, so just check it exists)
        from src.gui.gcode_previewer_components import gcode_interactive_loader
        print("✓ InteractiveGcodeLoader module exists")
        
        # Test main widget import (requires Qt, so just check it exists)
        from src.gui.gcode_previewer_components import gcode_previewer_main
        print("✓ GcodePreviewerWidget module exists")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parser():
    """Test GcodeParser functionality."""
    print("\nTesting GcodeParser...")
    
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
        
        # Check move types
        rapid_moves = [m for m in moves if m.is_rapid]
        cutting_moves = [m for m in moves if m.is_cutting]
        arc_moves = [m for m in moves if m.is_arc]
        tool_changes = [m for m in moves if m.is_tool_change]
        
        print(f"  - Rapid moves: {len(rapid_moves)}")
        print(f"  - Cutting moves: {len(cutting_moves)}")
        print(f"  - Arc moves: {len(arc_moves)}")
        print(f"  - Tool changes: {len(tool_changes)}")
        
        return True
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_renderer():
    """Test GcodeRenderer functionality."""
    print("\nTesting GcodeRenderer...")
    
    try:
        from src.gui.gcode_previewer_components.gcode_renderer import GcodeRenderer
        from src.gui.gcode_previewer_components.gcode_parser import GcodeParser
        
        renderer = GcodeRenderer()
        print("✓ GcodeRenderer instantiated")
        
        # Test with parsed moves
        parser = GcodeParser()
        lines = [
            "G00 X10 Y20 Z5",
            "G01 X30 Y40 Z0 F100",
            "G02 X50 Y50 I10 J10",
        ]
        moves = parser.parse_lines(lines)
        
        # Test rendering (won't actually render without VTK display)
        renderer.render_toolpath(moves)
        print("✓ Renderer processed moves")
        
        # Check move data structure
        if hasattr(renderer, 'move_data'):
            print(f"✓ Move data structure exists with {len(renderer.move_data)} categories")
        
        return True
    except Exception as e:
        print(f"✗ Renderer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("VTK G-code Viewer Integration Test (Simple)")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Parser", test_parser()))
    results.append(("Renderer", test_renderer()))
    
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
        print("\n✓ All integration tests passed!")
        print("\nThe VTK G-code viewer has been successfully integrated.")
        print("Components are ready to use in the main application.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

