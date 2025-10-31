#!/usr/bin/env python3
"""
Debug diagnostic to track theme values during startup vs preferences dialog.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_theme_values():
    """Debug what theme values are being retrieved at different points."""
    print("=" * 60)
    print("THEME VALUE DEBUGGING")
    print("=" * 60)
    
    try:
        from src.gui.theme.simple_service import ThemeService
        
        # Test 1: Check what get_current_theme() returns initially
        print("\n1. INITIAL THEME SERVICE STATE:")
        service = ThemeService.instance()
        theme, library = service.get_current_theme()
        variant = service.settings.value("qt_material_variant", "blue")
        
        print(f"   get_current_theme(): theme='{theme}', library='{library}'")
        print(f"   settings variant: '{variant}'")
        
        # Test 2: Simulate main application startup theme application
        print("\n2. MAIN APPLICATION STARTUP SIMULATION:")
        print("   Calling service.apply_theme() with retrieved values...")
        result = service.apply_theme(theme, library)
        print(f"   apply_theme() result: {result}")
        
        # Check what get_current_theme() returns after application
        theme2, library2 = service.get_current_theme()
        variant2 = service.settings.value("qt_material_variant", "blue")
        
        print(f"   After apply_theme() - theme='{theme2}', library='{library2}'")
        print(f"   After apply_theme() - variant='{variant2}'")
        
        # Test 3: Simulate preferences dialog theme application
        print("\n3. PREFERENCES DIALOG THEME SIMULATION:")
        print("   Calling _apply_qt_material_theme() logic...")
        
        # This is the logic from preferences.py
        current_theme, current_library = service.get_current_theme()
        current_variant = service.settings.value("qt_material_variant", "blue")
        
        print(f"   Retrieved for preferences: theme='{current_theme}', library='{current_library}'")
        print(f"   Retrieved for preferences: variant='{current_variant}'")
        
        # Check if defaults are needed
        if not current_theme or current_theme == "":
            print("   ⚠️  No theme set, would default to dark/blue")
            current_theme = "dark"
            service.set_qt_material_variant("blue")
        else:
            print("   ✅ Theme already set")
        
        # Apply theme again
        result2 = service.apply_theme(current_theme, current_library)
        print(f"   Preferences apply_theme() result: {result2}")
        
        # Final state
        final_theme, final_library = service.get_current_theme()
        final_variant = service.settings.value("qt_material_variant", "blue")
        
        print(f"   Final state - theme='{final_theme}', library='{final_library}'")
        print(f"   Final state - variant='{final_variant}'")
        
        # Analysis
        print("\n" + "=" * 60)
        print("ANALYSIS:")
        print("=" * 60)
        
        if theme == current_theme and variant == current_variant:
            print("✅ SAME THEME: Startup and preferences use identical theme values")
            print("   → The issue might be in qt-material application timing")
        else:
            print("❌ DIFFERENT THEME: Startup and preferences use different theme values!")
            print(f"   Startup: theme='{theme}', variant='{variant}'")
            print(f"   Preferences: theme='{current_theme}', variant='{current_variant}'")
            print("   → This explains the visual difference")
        
        # Check if theme was applied twice
        if result and result2:
            print("⚠️  THEME APPLIED TWICE: Both startup and preferences called apply_theme()")
            print("   → This might cause conflicts or overrides")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_theme_values()