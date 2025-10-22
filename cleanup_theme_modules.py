"""
Cleanup script for theme system consolidation.

This script removes the old fragmented theme modules after the consolidation
has been validated. It moves the old modules to a backup directory for safety
before deletion.

Usage:
    python cleanup_theme_modules.py [--keep-backup]
    
Options:
    --keep-backup: Keep the backup directory instead of deleting it
"""

import argparse
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def backup_old_modules(backup_dir: Path) -> bool:
    """Create backup of old theme modules."""
    logger.info("Creating backup of old theme modules...")
    
    try:
        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # List of old modules to backup
        old_modules = [
            "src/gui/theme/theme_constants.py",
            "src/gui/theme/theme_defaults.py",
            "src/gui/theme/theme_palette.py",
            "src/gui/theme/presets.py",
            "src/gui/theme/persistence.py",
            "src/gui/theme/service.py",
            "src/gui/theme/simple_service.py",
            "src/gui/theme/theme_api.py",
            "src/gui/theme/detector.py",
            "src/gui/theme/manager.py",
            "src/gui/theme/theme_manager_core.py",
            "src/gui/theme/ui/__init__.py",
            "src/gui/theme/ui/theme_switcher.py",
            "src/gui/theme/ui/simple_theme_switcher.py",
            "src/gui/theme/ui/qt_material_color_picker.py",
            "src/gui/theme/ui/theme_dialog.py",
        ]
        
        # Copy each module to backup
        for module_path in old_modules:
            src = Path(module_path)
            if src.exists():
                dst = backup_dir / src.name
                if src.parent.name == "ui":
                    # Create subdirectory in backup for ui modules
                    ui_backup_dir = backup_dir / "ui"
                    ui_backup_dir.mkdir(exist_ok=True)
                    dst = ui_backup_dir / src.name
                shutil.copy2(src, dst)
                logger.info(f"Backed up: {src} -> {dst}")
            else:
                logger.warning(f"Module not found: {src}")
        
        logger.info(f"Backup created at: {backup_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False


def remove_old_modules() -> bool:
    """Remove the old fragmented theme modules."""
    logger.info("Removing old theme modules...")
    
    try:
        # List of old modules to remove
        old_modules = [
            "src/gui/theme/theme_constants.py",
            "src/gui/theme/theme_defaults.py",
            "src/gui/theme/theme_palette.py",
            "src/gui/theme/presets.py",
            "src/gui/theme/persistence.py",
            "src/gui/theme/service.py",
            "src/gui/theme/simple_service.py",
            "src/gui/theme/theme_api.py",
            "src/gui/theme/detector.py",
            "src/gui/theme/manager.py",
            "src/gui/theme/theme_manager_core.py",
            "src/gui/theme/ui/__init__.py",
            "src/gui/theme/ui/theme_switcher.py",
            "src/gui/theme/ui/simple_theme_switcher.py",
            "src/gui/theme/ui/qt_material_color_picker.py",
            "src/gui/theme/ui/theme_dialog.py",
        ]
        
        # Remove each module
        for module_path in old_modules:
            src = Path(module_path)
            if src.exists():
                src.unlink()
                logger.info(f"Removed: {src}")
            else:
                logger.warning(f"Module not found: {src}")
        
        # Remove empty ui directory if it exists
        ui_dir = Path("src/gui/theme/ui")
        if ui_dir.exists() and not any(ui_dir.iterdir()):
            ui_dir.rmdir()
            logger.info(f"Removed empty directory: {ui_dir}")
        
        logger.info("Old theme modules removed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove old modules: {e}")
        return False


def verify_consolidation() -> bool:
    """Verify that the consolidation is working correctly."""
    logger.info("Verifying theme system consolidation...")
    
    try:
        # Test importing the new consolidated system
        from src.gui.theme import (
            ThemeService,
            ThemeManager,
            COLORS,
            color,
            qcolor,
            vtk_rgb,
            theme_to_dict,
            set_theme,
            list_theme_presets,
            apply_theme_preset,
            load_theme_from_settings,
            save_theme_to_settings,
            PRESET_LIGHT,
            get_preset,
            list_presets,
            SPACING_4,
            FALLBACK_COLOR,
            hex_to_rgb,
            hex_to_qcolor,
            hex_to_vtk_rgb,
            ThemeDefaults,
            ThemePersistence,
            ThemeSwitcher,
            SimpleThemeSwitcher,
            QtMaterialColorPicker,
            ThemeDialog,
        )
        
        # Test that the service works
        service = ThemeService.instance()
        assert service is not None, "ThemeService should be available"
        
        # Test that the manager works
        manager = ThemeManager.instance()
        assert manager is not None, "ThemeManager should be available"
        
        # Test that color functions work
        primary_color = color('primary')
        assert isinstance(primary_color, str), "color() should return a string"
        
        # Test that presets work
        presets = list_presets()
        assert len(presets) > 0, "Should have at least one preset"
        
        logger.info("✓ Theme system consolidation verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Theme system consolidation verification failed: {e}")
        return False


def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description="Cleanup old theme modules after consolidation")
    parser.add_argument("--keep-backup", action="store_true", help="Keep the backup directory")
    args = parser.parse_args()
    
    logger.info("Starting theme system cleanup...")
    
    # Create backup directory
    backup_dir = Path("theme_modules_backup")
    
    # Step 1: Verify consolidation is working
    if not verify_consolidation():
        logger.error("Consolidation verification failed. Aborting cleanup.")
        return False
    
    # Step 2: Create backup of old modules
    if not backup_old_modules(backup_dir):
        logger.error("Backup creation failed. Aborting cleanup.")
        return False
    
    # Step 3: Remove old modules
    if not remove_old_modules():
        logger.error("Module removal failed.")
        return False
    
    # Step 4: Remove backup if requested
    if not args.keep_backup:
        try:
            shutil.rmtree(backup_dir)
            logger.info(f"Removed backup directory: {backup_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove backup directory: {e}")
    
    logger.info("✓ Theme system cleanup completed successfully")
    logger.info("The theme system has been consolidated from 11+ modules to 4 focused modules:")
    logger.info("  - theme_core.py: Core theme data and configuration")
    logger.info("  - theme_service.py: Unified API for theme operations")
    logger.info("  - theme_ui.py: Theme-related UI components")
    logger.info("  - __init__.py: Clean public API with backward compatibility")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)