"""G-code Renderer - VTK-based 3D visualization of G-code toolpaths."""

from typing import List, Optional
import vtk
from .gcode_parser import GcodeMove


class GcodeRenderer:
    """Renders G-code toolpaths using VTK."""

    def __init__(self):
        """Initialize the renderer."""
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Set background color (dark theme)
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        
        self.actors = []
        self.bounds = None

    def render_toolpath(self, moves: List[GcodeMove]) -> None:
        """Render a list of G-code moves as a 3D toolpath."""
        if not moves:
            return
        
        # Clear previous actors
        for actor in self.actors:
            self.renderer.RemoveActor(actor)
        self.actors = []
        
        # Create separate polydata for different move types
        rapid_points = vtk.vtkPoints()
        cutting_points = vtk.vtkPoints()
        arc_points = vtk.vtkPoints()
        
        rapid_lines = vtk.vtkCellArray()
        cutting_lines = vtk.vtkCellArray()
        arc_lines = vtk.vtkCellArray()
        
        prev_point = None
        
        for move in moves:
            if move.x is None or move.y is None or move.z is None:
                continue
            
            current_point = (move.x, move.y, move.z)
            
            if prev_point is not None:
                # Add line segment
                if move.is_rapid:
                    self._add_line_segment(rapid_points, rapid_lines, prev_point, current_point)
                elif move.is_cutting:
                    self._add_line_segment(cutting_points, cutting_lines, prev_point, current_point)
                elif move.is_arc:
                    self._add_line_segment(arc_points, arc_lines, prev_point, current_point)
            
            prev_point = current_point
        
        # Create actors for each move type
        if rapid_points.GetNumberOfPoints() > 0:
            actor = self._create_actor(rapid_points, rapid_lines, (1.0, 0.5, 0.0), 2.0)  # Orange
            self.renderer.AddActor(actor)
            self.actors.append(actor)
        
        if cutting_points.GetNumberOfPoints() > 0:
            actor = self._create_actor(cutting_points, cutting_lines, (0.0, 1.0, 0.0), 3.0)  # Green
            self.renderer.AddActor(actor)
            self.actors.append(actor)
        
        if arc_points.GetNumberOfPoints() > 0:
            actor = self._create_actor(arc_points, arc_lines, (0.0, 0.5, 1.0), 2.5)  # Cyan
            self.renderer.AddActor(actor)
            self.actors.append(actor)
        
        # Add axes
        self._add_axes()
        
        # Reset camera
        self.renderer.ResetCamera()

    def _add_line_segment(self, points: vtk.vtkPoints, lines: vtk.vtkCellArray,
                         start: tuple, end: tuple) -> None:
        """Add a line segment to the polydata."""
        start_id = points.InsertNextPoint(start)
        end_id = points.InsertNextPoint(end)
        
        line = vtk.vtkLine()
        line.GetPointIds().SetId(0, start_id)
        line.GetPointIds().SetId(1, end_id)
        lines.InsertNextCell(line)

    def _create_actor(self, points: vtk.vtkPoints, lines: vtk.vtkCellArray,
                     color: tuple, line_width: float) -> vtk.vtkActor:
        """Create a VTK actor from points and lines."""
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        
        return actor

    def _add_axes(self) -> None:
        """Add coordinate axes to the scene."""
        axes = vtk.vtkAxesActor()
        axes.SetScale(10.0)
        
        # Create a transform to position the axes
        transform = vtk.vtkTransform()
        transform.Translate(0, 0, 0)
        axes.SetUserTransform(transform)
        
        self.renderer.AddActor(axes)

    def get_renderer(self) -> vtk.vtkRenderer:
        """Get the VTK renderer."""
        return self.renderer

    def get_render_window(self) -> vtk.vtkRenderWindow:
        """Get the VTK render window."""
        return self.render_window

    def reset_camera(self) -> None:
        """Reset camera to fit all actors."""
        self.renderer.ResetCamera()

    def set_background_color(self, r: float, g: float, b: float) -> None:
        """Set renderer background color."""
        self.renderer.SetBackground(r, g, b)

