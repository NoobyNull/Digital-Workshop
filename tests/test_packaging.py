#!/usr/bin/env python3
"""
3D-MM (3D Model Manager) - Packaging Tests

This module contains tests for the packaging components to ensure
the build and installation process works correctly.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.settings_migration import SettingsMigrator


class TestSettingsMigration(unittest.TestCase):
    """Test the settings migration functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.app_name = "3D-MM-Test"
        
        # Create mock migrator with test directory
        with patch('core.settings_migration.QStandardPaths') as mock_paths:
            mock_paths.writableLocation.return_value = str(self.test_dir / "app_data")
            self.migrator = SettingsMigrator(self.app_name)
            
        # Set up paths for testing
        self.migrator.app_data_path = self.test_dir / "app_data"
        self.migrator.old_app_data_path = self.test_dir / "old_app_data"
        self.migrator.current_db_path = self.migrator.app_data_path / "3dmm.db"
        self.migrator.old_db_path = self.migrator.old_app_data_path / "3dmm.db"
        self.migrator.settings_path = self.migrator.app_data_path / "settings.json"
        self.migrator.old_settings_path = self.migrator.old_app_data_path / "settings.json"
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_no_migration_needed_new_install(self):
        """Test that migration is not needed for new installations."""
        # No old data exists
        result = self.migrator.check_migration_needed()
        self.assertFalse(result)
    
    def test_migration_needed_old_install_exists(self):
        """Test that migration is needed when old installation exists."""
        # Create old installation directory
        self.migrator.old_app_data_path.mkdir(parents=True)
        
        result = self.migrator.check_migration_needed()
        self.assertTrue(result)
    
    def test_get_old_version_from_settings(self):
        """Test getting old version from settings file."""
        # Create old settings with version
        self.migrator.old_app_data_path.mkdir(parents=True)
        old_settings = {"version": "0.9.0", "theme": "dark"}
        with open(self.migrator.old_settings_path, 'w') as f:
            json.dump(old_settings, f)
        
        version = self.migrator._get_old_version()
        self.assertEqual(version, "0.9.0")
    
    def test_merge_settings(self):
        """Test merging old settings with current defaults."""
        old_settings = {
            "theme": "dark",
            "window_geometry": "custom_geometry",
            "recent_files": ["file1.stl", "file2.obj"]
        }
        
        current_settings = {
            "theme": "light",  # Default
            "language": "en",
            "new_setting": "value"
        }
        
        merged = self.migrator._merge_settings(old_settings, current_settings)
        
        # Should preserve user customizations
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["window_geometry"], "custom_geometry")
        self.assertEqual(merged["recent_files"], ["file1.stl", "file2.obj"])
        
        # Should keep new defaults
        self.assertEqual(merged["language"], "en")
        self.assertEqual(merged["new_setting"], "value")
    
    def test_create_backup(self):
        """Test creating a backup of current settings."""
        # Create some app data
        self.migrator.app_data_path.mkdir(parents=True)
        test_file = self.migrator.app_data_path / "test.txt"
        test_file.write_text("test content")
        
        result = self.migrator.create_backup()
        self.assertTrue(result)
        
        # Check backup was created
        backup_dirs = list(self.test_dir.glob("3D-MM-Test_backup_*"))
        self.assertEqual(len(backup_dirs), 1)
        
        backup_file = backup_dirs[0] / "test.txt"
        self.assertTrue(backup_file.exists())
        self.assertEqual(backup_file.read_text(), "test content")
    
    def test_migrate_settings_file(self):
        """Test migrating settings file from old to new location."""
        # Create old settings
        self.migrator.old_app_data_path.mkdir(parents=True)
        old_settings = {
            "version": "0.9.0",
            "theme": "dark",
            "window_geometry": "custom_geometry"
        }
        with open(self.migrator.old_settings_path, 'w') as f:
            json.dump(old_settings, f)
        
        # Create current settings directory
        self.migrator.app_data_path.mkdir(parents=True)
        
        # Migrate settings
        self.migrator._migrate_settings_file()
        
        # Check settings were migrated
        self.assertTrue(self.migrator.settings_path.exists())
        with open(self.migrator.settings_path, 'r') as f:
            migrated_settings = json.load(f)
        
        self.assertEqual(migrated_settings["theme"], "dark")
        self.assertEqual(migrated_settings["window_geometry"], "custom_geometry")


class TestBuildConfiguration(unittest.TestCase):
    """Test the build configuration and scripts."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(tempfile.mkdtemp())
        
        # Create minimal project structure
        (self.project_root / "src").mkdir()
        (self.project_root / "src" / "main.py").write_text("# Main entry point")
        (self.project_root / "pyinstaller.spec").write_text("# PyInstaller spec")
        (self.project_root / "requirements.txt").write_text("PySide5>=5.15.0")
    
    def tearDown(self):
        """Clean up test environment."""
        if self.project_root.exists():
            shutil.rmtree(self.project_root)
    
    def test_pyinstaller_spec_exists(self):
        """Test that PyInstaller spec file exists and has required content."""
        spec_file = self.project_root / "pyinstaller.spec"
        self.assertTrue(spec_file.exists())
        
        content = spec_file.read_text()
        self.assertIn("Analysis", content)
        self.assertIn("EXE", content)
        self.assertIn("3D-MM", content)
    
    def test_build_script_exists(self):
        """Test that build script exists and is importable."""
        build_script = Path(__file__).parent.parent / "build.py"
        self.assertTrue(build_script.exists())
        
        # Test that build script can be imported
        sys.path.insert(0, str(build_script.parent))
        try:
            import build
            self.assertTrue(hasattr(build, 'BuildManager'))
        finally:
            sys.path.remove(str(build_script.parent))
    
    def test_batch_file_exists(self):
        """Test that Windows batch file exists."""
        batch_file = Path(__file__).parent.parent / "installer" / "build.bat"
        self.assertTrue(batch_file.exists())
        
        content = batch_file.read_text()
        self.assertIn("python", content.lower())
        self.assertIn("build.py", content.lower())


class TestInstallerAssets(unittest.TestCase):
    """Test the installer assets and configuration."""
    
    def setUp(self):
        """Set up test environment."""
        self.installer_dir = Path(__file__).parent.parent / "installer"
        self.assets_dir = self.installer_dir / "assets"
    
    def test_installer_script_exists(self):
        """Test that Inno Setup script exists."""
        installer_script = self.installer_dir / "inno_setup.iss"
        self.assertTrue(installer_script.exists())
        
        content = installer_script.read_text()
        self.assertIn("[Setup]", content)
        self.assertIn("3D-MM", content)
        self.assertIn("File association", content)
    
    def test_required_assets_exist(self):
        """Test that required installer assets exist."""
        license_file = self.assets_dir / "license.txt"
        readme_file = self.assets_dir / "readme.txt"
        
        self.assertTrue(license_file.exists(), "License file should exist")
        self.assertTrue(readme_file.exists(), "Readme file should exist")
        
        # Check content
        license_content = license_file.read_text()
        self.assertIn("LICENSE AGREEMENT", license_content)
        
        readme_content = readme_file.read_text()
        self.assertIn("SYSTEM REQUIREMENTS", readme_content)
    
    def test_file_associations_configured(self):
        """Test that file associations are properly configured."""
        installer_script = self.installer_dir / "inno_setup.iss"
        content = installer_script.read_text()
        
        # Check for supported file extensions
        extensions = [".stl", ".obj", ".3mf", ".step", ".stp"]
        for ext in extensions:
            self.assertIn(ext, content, f"File association for {ext} should be configured")


class TestBuildProcess(unittest.TestCase):
    """Test the build process components."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
    
    def test_version_info_exists(self):
        """Test that version info file exists for Windows executable."""
        version_file = self.project_root / "version_info.txt"
        self.assertTrue(version_file.exists())
        
        content = version_file.read_text()
        self.assertIn("VSVersionInfo", content)
        self.assertIn("3D-MM", content)
        self.assertIn("1.0.0", content)
    
    def test_documentation_exists(self):
        """Test that packaging documentation exists."""
        docs_file = self.project_root / "docs" / "developer" / "packaging_documentation.md"
        self.assertTrue(docs_file.exists())
        
        content = docs_file.read_text()
        self.assertIn("Build System Components", content)
        self.assertIn("PyInstaller", content)
        self.assertIn("Inno Setup", content)


if __name__ == "__main__":
    unittest.main()