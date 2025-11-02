"""
Test material application functionality for 3D models.

This test validates that materials can be properly applied to 3D models
when the Materials button is clicked in the VTK viewer.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.core.material_provider import MaterialProvider
from src.gui.material_components.material_manager_main import MaterialManager
from src.gui.materials.integration import MaterialLightingIntegrator
from src.core.data_structures import ModelFormat


class TestMaterialApplication(unittest.TestCase):
    """Test material application functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary materials directory with test files
        self.temp_dir = tempfile.mkdtemp()
        self.materials_dir = Path(self.temp_dir) / "materials"
        self.materials_dir.mkdir()
        
        # Create test material files
        self.test_material_name = "test_wood"
        self.test_texture_path = self.materials_dir / f"{self.test_material_name}.png"
        self.test_mtl_path = self.materials_dir / f"{self.test_material_name}.mtl"
        
        # Create a simple PNG file (just a placeholder)
        with open(self.test_texture_path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # Minimal PNG header
            
        # Create MTL file with material properties
        with open(self.test_mtl_path, "w") as f:
            f.write(f"""newmtl {self.test_material_name}
Ka 0.2 0.2 0.2
Kd 0.8 0.6 0.4
Ks 0.1 0.1 0.1
Ns 10.0
d 1.0
""")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_material_provider_discovers_materials(self):
        """Test that MaterialProvider can discover materials."""
        # Temporarily override the default materials directory
        with patch.object(MaterialProvider, 'DEFAULT_MATERIALS_DIR', self.materials_dir):
            provider = MaterialProvider()
            materials = provider.get_available_materials()
            
            self.assertEqual(len(materials), 1)
            self.assertEqual(materials[0]['name'], self.test_material_name)
            self.assertEqual(materials[0]['texture_path'], self.test_texture_path)
            self.assertEqual(materials[0]['mtl_path'], self.test_mtl_path)

    def test_material_provider_get_by_name(self):
        """Test that MaterialProvider can get materials by name."""
        with patch.object(MaterialProvider, 'DEFAULT_MATERIALS_DIR', self.materials_dir):
            provider = MaterialProvider()
            material = provider.get_material_by_name(self.test_material_name)
            
            self.assertIsNotNone(material)
            self.assertEqual(material['name'], self.test_material_name)
            self.assertEqual(material['texture_path'], self.test_texture_path)
            self.assertEqual(material['mtl_path'], self.test_mtl_path)

    def test_material_provider_mtl_parsing(self):
        """Test that MaterialProvider can parse MTL files."""
        with patch.object(MaterialProvider, 'DEFAULT_MATERIALS_DIR', self.materials_dir):
            provider = MaterialProvider()
            material = provider.get_material_by_name(self.test_material_name)
            
            self.assertIn('properties', material)
            properties = material['properties']
            
            # Check that MTL properties were parsed correctly
            self.assertEqual(properties['diffuse'], (0.8, 0.6, 0.4))
            self.assertEqual(properties['ambient'], (0.2, 0.2, 0.2))
            self.assertEqual(properties['specular'], (0.1, 0.1, 0.1))
            self.assertEqual(properties['shininess'], 10.0)

    def test_material_lighting_integrator_stl_material_application(self):
        """Test that MaterialLightingIntegrator can apply STL materials."""
        # Create mock objects
        mock_main_window = Mock()
        mock_viewer_widget = Mock()
        mock_actor = Mock()
        mock_viewer_widget.actor = mock_actor
        mock_main_window.viewer_widget = mock_viewer_widget
        
        # Mock current model with STL format
        mock_model = Mock()
        mock_model.format_type = ModelFormat.STL
        mock_viewer_widget.current_model = mock_model
        
        # Create mock material manager and provider
        mock_material_manager = Mock()
        mock_material_provider = Mock()
        mock_material_manager.material_provider = mock_material_provider
        
        # Set up the material provider to return our test material
        test_material = {
            'name': self.test_material_name,
            'texture_path': self.test_texture_path,
            'mtl_path': self.test_mtl_path,
            'properties': {
                'diffuse': (0.8, 0.6, 0.4),
                'ambient': (0.2, 0.2, 0.2),
                'specular': (0.1, 0.1, 0.1),
                'shininess': 10.0
            }
        }
        mock_material_provider.get_material_by_name.return_value = test_material
        mock_material_manager.apply_material_to_actor.return_value = True
        
        mock_main_window.material_manager = mock_material_manager
        
        # Create integrator and apply material
        integrator = MaterialLightingIntegrator(mock_main_window)
        
        # Test STL material application (no texture)
        with patch.object(MaterialProvider, 'DEFAULT_MATERIALS_DIR', self.materials_dir):
            integrator.apply_material_species(self.test_material_name)
            
            # Verify that the material was applied
            mock_material_manager.apply_material_to_actor.assert_called_once()

    def test_material_lighting_integrator_method_names(self):
        """Test that MaterialLightingIntegrator has correct method names."""
        mock_main_window = Mock()
        integrator = MaterialLightingIntegrator(mock_main_window)
        
        # Test that the public methods exist and are callable
        self.assertTrue(hasattr(integrator, 'apply_material_species'))
        self.assertTrue(hasattr(integrator, 'apply_stl_material_properties'))
        self.assertTrue(hasattr(integrator, 'parse_mtl_direct'))
        self.assertTrue(callable(integrator.apply_material_species))
        self.assertTrue(callable(integrator.apply_stl_material_properties))
        self.assertTrue(callable(integrator.parse_mtl_direct))

    def test_material_manager_apply_to_actor(self):
        """Test that MaterialManager can apply materials to VTK actors."""
        # Create mock database manager
        mock_db_manager = Mock()
        
        # Create material manager
        with patch.object(MaterialProvider, 'DEFAULT_MATERIALS_DIR', self.materials_dir):
            material_manager = MaterialManager(mock_db_manager)
            
            # Create mock VTK actor
            mock_actor = Mock()
            
            # Test material application
            result = material_manager.apply_material_to_actor(mock_actor, self.test_material_name)
            
            # The result should be True if material was found and applied
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()