"""
Test the camera headlight system implementation.

Tests that the headlight:
1. Is created correctly in VTKSceneManager
2. Follows camera position when camera moves
3. Uses theme colors
4. Preserves existing directional lights
5. Updates intensity correctly
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, 'src')

from src.gui.viewer_3d.vtk_scene_manager import VTKSceneManager
from src.gui.viewer_3d.camera_controller import CameraController
from src.gui.viewer_3d.viewer_widget_facade import Viewer3DWidget


class MockVTKWidget:
    """Mock VTK widget for testing."""
    def GetRenderWindow(self):
        return Mock()
    
    def GetRenderWindowInteractor(self):
        return Mock()


class MockCamera:
    """Mock VTK camera."""
    def __init__(self):
        self.position = (0, 0, 5)
        self.focal_point = (0, 0, 0)
        self.view_up = (0, 1, 0)
        
    def GetPosition(self):
        return self.position
        
    def GetFocalPoint(self):
        return self.focal_point
        
    def GetViewUp(self):
        return self.view_up
        
    def SetPosition(self, x, y, z):
        self.position = (x, y, z)
        
    def SetFocalPoint(self, x, y, z):
        self.focal_point = (x, y, z)
        
    def SetViewUp(self, x, y, z):
        self.view_up = (x, y, z)


class MockRenderer:
    """Mock VTK renderer."""
    def __init__(self):
        self.lights = []
        self.camera = MockCamera()
        self.background = (0.1, 0.1, 0.1)
        self.background2 = (0.0, 0.0, 0.0)
        
    def AddLight(self, light):
        self.lights.append(light)
        
    def GetLights(self):
        mock_lights = Mock()
        mock_lights.GetNumberOfItems.return_value = len(self.lights)
        mock_lights.GetItemAsObject = Mock(side_effect=lambda i: self.lights[i])
        return mock_lights
        
    def GetActiveCamera(self):
        return self.camera
        
    def SetActiveCamera(self, camera):
        self.camera = camera
        
    def SetBackground(self, r, g, b):
        self.background = (r, g, b)
        
    def SetBackground2(self, r, g, b):
        self.background2 = (r, g, b)
        
    def GradientBackgroundOn(self):
        pass
        
    def ResetCamera(self):
        pass
        
    def ResetCameraClippingRange(self):
        pass


class MockLight:
    """Mock VTK light."""
    def __init__(self):
        self.position = (0, 0, 1)
        self.focal_point = (0, 0, 0)
        self.intensity = 1.0
        self.color = (1.0, 1.0, 1.0)
        self.type = 'SceneLight'
        self.switch = 1  # 1 = on, 0 = off
        
    def SetPosition(self, x, y, z):
        self.position = (x, y, z)
        
    def SetFocalPoint(self, x, y, z):
        self.focal_point = (x, y, z)
        
    def SetIntensity(self, intensity):
        self.intensity = intensity
        
    def SetColor(self, r, g, b):
        self.color = (r, g, b)
        
    def SetLightTypeToPointLight(self):
        self.type = 'PointLight'
        
    def SetAttenuationValues(self, a, b, c):
        pass
        
    def SetSwitch(self, switch_state):
        self.switch = switch_state
        
    def GetPosition(self):
        return self.position
        
    def GetFocalPoint(self):
        return self.focal_point
        
    def GetIntensity(self):
        return self.intensity
        
    def GetColor(self):
        return self.color
        
    def GetSwitch(self):
        return self.switch


@pytest.fixture
def mock_vtk():
    """Mock VTK module."""
    with patch('src.gui.viewer_3d.vtk_scene_manager.vtk') as mock_vtk:
        # Mock VTK classes
        mock_vtk.vtkRenderer = MockRenderer
        mock_vtk.vtkLight = MockLight
        mock_vtk.vtkCamera = MockCamera
        
        # Mock other VTK components
        mock_vtk.vtkMultiThreader = Mock()
        mock_vtk.vtkSMPTools = Mock()
        
        yield mock_vtk


@pytest.fixture
def mock_color_provider():
    """Mock color provider."""
    with patch('src.gui.viewer_3d.vtk_scene_manager.get_vtk_color_provider') as mock:
        provider = Mock()
        provider.get_vtk_color = Mock(side_effect=lambda color_name: {
            'canvas_bg': (0.2, 0.2, 0.2),
            'light_color': (1.0, 1.0, 0.9),
            'edge_color': (0.5, 0.5, 0.5),
            'grid_color': (0.7, 0.7, 0.7),
            'ground_color': (0.5, 0.5, 0.5)
        }.get(color_name, (0.5, 0.5, 0.5)))
        provider.register_vtk_manager = Mock()
        mock.return_value = provider
        yield provider


@pytest.fixture
def scene_manager(mock_vtk, mock_color_provider):
    """Create VTKSceneManager for testing."""
    vtk_widget = MockVTKWidget()
    manager = VTKSceneManager(vtk_widget)
    manager.setup_scene()
    return manager


def test_headlight_creation(scene_manager):
    """Test that headlight is created correctly."""
    # Check that headlight exists
    assert scene_manager.headlight is not None, "Headlight should be created"
    
    # Check that headlight is a point light
    assert scene_manager.headlight.type == 'PointLight', "Headlight should be a point light"
    
    # Check default intensity
    assert scene_manager.headlight_intensity == 0.6, "Default headlight intensity should be 0.6"
    assert scene_manager.headlight.intensity == 0.6, "Headlight intensity should match setting"
    
    # Check that we have 3 lights total (2 directional + 1 headlight)
    assert len(scene_manager.renderer.lights) == 3, "Should have 3 lights total"


def test_existing_lights_preserved(scene_manager):
    """Test that existing directional lights are preserved."""
    lights = scene_manager.renderer.lights
    
    # First two lights should be directional lights
    assert lights[0].type == 'SceneLight', "First light should be directional"
    assert lights[1].type == 'SceneLight', "Second light should be directional"
    
    # Check their positions
    assert lights[0].position == (100, 100, 100), "First light should be at (100, 100, 100)"
    assert lights[1].position == (-100, -100, 100), "Second light should be at (-100, -100, 100)"
    
    # Check their intensities
    assert lights[0].intensity == 0.8, "First light intensity should be 0.8"
    assert lights[1].intensity == 0.5, "Second light intensity should be 0.5"


def test_headlight_follows_camera(scene_manager):
    """Test that headlight follows camera position."""
    camera = scene_manager.renderer.camera
    
    # Move camera
    camera.SetPosition(10, 20, 30)
    camera.SetFocalPoint(0, 0, 0)
    
    # Update headlight
    scene_manager.update_headlight_position()
    
    # Check headlight follows camera
    assert scene_manager.headlight.position == (10, 20, 30), "Headlight should follow camera position"
    assert scene_manager.headlight.focal_point == (0, 0, 0), "Headlight should point to camera focal point"


def test_headlight_intensity_setting(scene_manager):
    """Test headlight intensity can be changed."""
    # Set new intensity
    scene_manager.set_headlight_intensity(0.8)
    
    # Check intensity was updated
    assert scene_manager.headlight_intensity == 0.8, "Headlight intensity property should be updated"
    assert scene_manager.headlight.intensity == 0.8, "Headlight intensity should be updated"
    
    # Test bounds checking
    scene_manager.set_headlight_intensity(1.5)  # Should be clamped to 1.0
    assert scene_manager.headlight_intensity == 1.0, "Intensity should be clamped to maximum"
    
    scene_manager.set_headlight_intensity(-0.5)  # Should be clamped to 0.0
    assert scene_manager.headlight_intensity == 0.0, "Intensity should be clamped to minimum"


def test_headlight_theme_color_update(scene_manager):
    """Test headlight color updates with theme."""
    # Update theme colors
    scene_manager.update_theme_colors()
    
    # Check headlight color was updated
    assert scene_manager.headlight.color == (1.0, 1.0, 0.9), "Headlight should use theme light color"


def test_camera_controller_integration():
    """Test CameraController integration with headlight."""
    with patch('src.gui.viewer_3d.camera_controller.vtk') as mock_vtk:
        # Mock VTK classes
        mock_vtk.vtkCamera = MockCamera
        
        # Create mock renderer and scene manager
        renderer = MockRenderer()
        render_window = Mock()
        scene_manager = Mock()
        scene_manager.update_headlight_position = Mock()
        
        # Create camera controller with scene manager
        controller = CameraController(renderer, render_window, scene_manager)
        
        # Test that headlight is updated after camera operations
        controller.reset_view()
        scene_manager.update_headlight_position.assert_called_once()


def test_viewer_widget_facade_integration():
    """Test Viewer3DWidget integration."""
    with patch('src.gui.viewer_3d.viewer_widget_facade.vtk') as mock_vtk, \
         patch('src.gui.viewer_3d.viewer_widget_facade.ViewerUIManager') as mock_ui:
        
        # Mock VTK classes
        mock_vtk.vtkRenderer = MockRenderer
        mock_vtk.vtkLight = MockLight
        mock_vtk.vtkCamera = MockCamera
        
        # Mock UI manager
        ui_manager = Mock()
        ui_manager.setup_ui = Mock()
        ui_manager.get_vtk_widget.return_value = MockVTKWidget()
        mock_ui.return_value = ui_manager
        
        # Create viewer widget
        widget = Viewer3DWidget()
        
        # Check that camera controller has scene manager reference
        assert widget.camera_controller.scene_manager is widget.scene_manager, \
            "Camera controller should have scene manager reference"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])