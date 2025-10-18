"""VTK Widget - Qt integration for VTK rendering."""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from .gcode_renderer import GcodeRenderer


class VTKWidget(QWidget):
    """Qt widget for VTK rendering."""
    
    def __init__(self, renderer: GcodeRenderer, parent: Optional[QWidget] = None):
        """Initialize the VTK widget."""
        super().__init__(parent)
        
        self.renderer = renderer
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VTK interactor
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)
        
        # Connect renderer to interactor
        self.vtk_widget.GetRenderWindow().AddRenderer(renderer.get_renderer())
        
        # Setup interactor style
        interactor_style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.GetInteractorStyle().SetInteractorStyle(interactor_style)
        
        # Initialize interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()
    
    def update_render(self) -> None:
        """Update the VTK render."""
        self.vtk_widget.GetRenderWindow().Render()
    
    def reset_camera(self) -> None:
        """Reset camera to fit all actors."""
        self.renderer.reset_camera()
        self.update_render()

