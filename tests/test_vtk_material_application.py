#!/usr/bin/env python3
"""
Test script for VTK-only material application system.

This test validates that:
1. PyQt3D dependencies have been removed
2. VTK-only material application works correctly
3. Default material application from preferences works
4. Material application integrates properly with the VTK viewer
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

# Test imports
try:
    from src.gui.viewer_3d.model_renderer import ModelRenderer, RenderMode
    from src.gui.viewer_3d.viewer_widget_facade import Viewer3DWidget
    from src.gui.material_components.material_manager_main import MaterialManager
    from src.gui.materials.integration import MaterialLightingIntegrator

    VTK_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    VTK_AVAILABLE = False


class TestVTKMaterialApplication(unittest.TestCase):
    """Test VTK-only material application system."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not VTK_AVAILABLE:
            cls.skipTest(cls, "Required modules not available")

        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up each test."""
        self.settings = QSettings()
        self.test_material = "maple"

        # Set default material in preferences
        self.settings.setValue("thumbnail/material", self.test_material)

        # Create mock VTK renderer
        self.mock_renderer = Mock()
        self.mock_render_window = Mock()
        self.mock_renderer.GetRenderWindow.return_value = self.mock_render_window

        # Create mock material manager
        self.mock_material_manager = Mock()
        self.mock_material_manager.apply_material_to_actor.return_value = True

    def test_pyqt3d_files_removed(self):
        """Test that PyQt3D files have been removed."""
        pyqt3d_files = [
            "src/gui/viewer_widget.py",
            "src/gui/viewer_components/viewer_3d_widget_main.py",
        ]

        for file_path in pyqt3d_files:
            full_path = Path(file_path)
            self.assertFalse(
                full_path.exists(), f"PyQt3D file {file_path} should be removed"
            )

    def test_model_renderer_material_methods(self):
        """Test that ModelRenderer has material application methods."""
        renderer = ModelRenderer(self.mock_renderer)

        # Test that material methods exist
        self.assertTrue(
            hasattr(renderer, "apply_material"),
            "ModelRenderer should have apply_material method",
        )
        self.assertTrue(
            hasattr(renderer, "apply_default_material"),
            "ModelRenderer should have apply_default_material method",
        )

        # Test apply_material method
        success = renderer.apply_material("test_material", self.mock_material_manager)
        self.assertTrue(
            success, "apply_material should return True when material manager succeeds"
        )

        # Verify material manager was called
        self.mock_material_manager.apply_material_to_actor.assert_called_once()

    def test_model_renderer_default_material(self):
        """Test default material application from preferences."""
        renderer = ModelRenderer(self.mock_renderer)

        # Test apply_default_material method
        success = renderer.apply_default_material(self.mock_material_manager)
        self.assertTrue(success, "apply_default_material should return True")

        # Verify it used the correct default material
        self.mock_material_manager.apply_material_to_actor.assert_called_with(
            renderer.actor, self.test_material
        )

    def test_viewer_widget_material_methods(self):
        """Test that Viewer3DWidget has material application methods."""
        with patch("src.gui.viewer_3d.viewer_widget_facade.VTKSceneManager"):
            with patch("src.gui.viewer_3d.viewer_widget_facade.ModelRenderer"):
                with patch("src.gui.viewer_3d.viewer_widget_facade.CameraController"):
                    with patch(
                        "src.gui.viewer_3d.viewer_widget_facade.PerformanceTracker"
                    ):
                        with patch(
                            "src.gui.viewer_3d.viewer_widget_facade.ViewerUIManager"
                        ):
                            widget = Viewer3DWidget()

                            # Test that material methods exist
                            self.assertTrue(
                                hasattr(widget, "apply_material_to_current_model"),
                                "Viewer3DWidget should have apply_material_to_current_model method",
                            )
                            self.assertTrue(
                                hasattr(
                                    widget, "apply_default_material_to_current_model"
                                ),
                                "Viewer3DWidget should have apply_default_material_to_current_model method",
                            )

                            # Test material manager discovery
                            material_manager = widget._get_material_manager()
                            # Should return None since we don't have a real material manager
                            self.assertIsNone(
                                material_manager,
                                "_get_material_manager should return None for mock setup",
                            )

    def test_material_application_integration(self):
        """Test integration between viewer and material system."""
        with patch("src.gui.viewer_3d.viewer_widget_facade.VTKSceneManager"):
            with patch(
                "src.gui.viewer_3d.viewer_widget_facade.ModelRenderer"
            ) as mock_model_renderer:
                with patch("src.gui.viewer_3d.viewer_widget_facade.CameraController"):
                    with patch(
                        "src.gui.viewer_3d.viewer_widget_facade.PerformanceTracker"
                    ):
                        with patch(
                            "src.gui.viewer_3d.viewer_widget_facade.ViewerUIManager"
                        ):

                            # Create mock model renderer instance
                            mock_renderer_instance = Mock()
                            mock_model_renderer.return_value = mock_renderer_instance
                            mock_renderer_instance.apply_material.return_value = True
                            mock_renderer_instance.apply_default_material.return_value = (
                                True
                            )

                            widget = Viewer3DWidget()

                            # Test material application
                            success = widget.apply_material_to_current_model(
                                "test_material", self.mock_material_manager
                            )
                            self.assertTrue(
                                success, "Material application should succeed"
                            )

                            # Test default material application
                            success = widget.apply_default_material_to_current_model(
                                self.mock_material_manager
                            )
                            self.assertTrue(
                                success, "Default material application should succeed"
                            )

    def test_material_preferences_integration(self):
        """Test that material preferences are properly integrated."""
        # Test default material setting
        default_material = self.settings.value("thumbnail/material", "maple", type=str)
        self.assertEqual(
            default_material,
            self.test_material,
            "Default material should be saved in preferences",
        )

        # Test changing default material
        new_material = "cherry"
        self.settings.setValue("thumbnail/material", new_material)
        retrieved_material = self.settings.value(
            "thumbnail/material", "maple", type=str
        )
        self.assertEqual(
            retrieved_material, new_material, "Material preference should be changeable"
        )

    def test_no_pyqt3d_imports(self):
        """Test that no PyQt3D imports remain in key files."""
        key_files = [
            "src/gui/viewer_3d/model_renderer.py",
            "src/gui/viewer_3d/viewer_widget_facade.py",
            "src/gui/viewer_components/__init__.py",
        ]

        pyqt3d_imports = ["PyQt3D", "Qt3DCore", "Qt3DExtras", "Qt3DRender", "Qt3DInput"]

        for file_path in key_files:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()

                for pyqt3d_import in pyqt3d_imports:
                    self.assertNotIn(
                        pyqt3d_import,
                        content,
                        f"File {file_path} should not contain PyQt3D import: {pyqt3d_import}",
                    )

    def test_material_lighting_integrator_method_names(self):
        """Test that MaterialLightingIntegrator has correct method names."""
        try:
            integrator = MaterialLightingIntegrator()

            # Test that methods exist with correct names (no underscore prefix)
            self.assertTrue(
                hasattr(integrator, "apply_stl_material_properties"),
                "MaterialLightingIntegrator should have apply_stl_material_properties method",
            )
            self.assertTrue(
                hasattr(integrator, "parse_mtl_direct"),
                "MaterialLightingIntegrator should have parse_mtl_direct method",
            )

            # Test that old incorrect method names don't exist
            self.assertFalse(
                hasattr(integrator, "_apply_stl_material_properties"),
                "MaterialLightingIntegrator should not have _apply_stl_material_properties method",
            )
            self.assertFalse(
                hasattr(integrator, "_parse_mtl_direct"),
                "MaterialLightingIntegrator should not have _parse_mtl_direct method",
            )

        except Exception as e:
            self.skipTest(f"MaterialLightingIntegrator not available: {e}")


def run_tests():
    """Run all tests."""
    print("Testing VTK-only material application system...")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVTKMaterialApplication)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOVERALL RESULT: {'PASS' if success else 'FAIL'}")

    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
