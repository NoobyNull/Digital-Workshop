"""G-code Renderer - VTK-based 3D visualization of G-code toolpaths."""

from typing import List, Optional, Dict, TYPE_CHECKING
from .gcode_parser import GcodeMove

# Type hints only import
if TYPE_CHECKING:
    import vtk as VtkModule


class GcodeRenderer:
    """Renders G-code toolpaths using VTK."""

    # Class-level vtk module (loaded once per class)
    _vtk_module: Optional["VtkModule"] = None

    def __init__(self):
        """Initialize the renderer."""
        # Lazy load VTK at instance creation
        self._ensure_vtk_loaded()

        # Use the class-level module
        vtk = self._vtk_module

        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        # Set background color (dark theme)
        self.renderer.SetBackground(0.2, 0.2, 0.2)

        self.actors: Dict[str, vtk.vtkActor] = {}
        self.bounds = None

        # For incremental rendering - organize by move type
        self.move_data = {
            "rapid": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "actor": None,
            },
            "cutting": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "actor": None,
            },
            "arc": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "actor": None,
            },
            "tool_change": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "actor": None,
            },
        }
        self.prev_point = None

        # Color scheme for different move types
        self.colors = {
            "rapid": (1.0, 0.5, 0.0),  # Orange - fast moves
            "cutting": (0.0, 1.0, 0.0),  # Green - cutting moves
            "arc": (0.0, 0.5, 1.0),  # Cyan - arc moves
            "tool_change": (1.0, 0.0, 1.0),  # Magenta - tool changes
        }

        # Line widths for different move types
        self.line_widths = {
            "rapid": 1.5,
            "cutting": 3.0,
            "arc": 2.5,
            "tool_change": 2.0,
        }

    @classmethod
    def _ensure_vtk_loaded(cls) -> None:
        """Ensure VTK module is loaded (once per class)."""
        if cls._vtk_module is None:
            try:
                import vtk as vtk_module

                cls._vtk_module = vtk_module
            except ImportError as e:
                raise ImportError(
                    "VTK is required for G-code rendering. " "Install with: pip install vtk"
                ) from e

    @property
    def vtk(self):
        """Access VTK module."""
        return self._vtk_module

    def render_toolpath(self, moves: List[GcodeMove]) -> None:
        """Render a list of G-code moves as a 3D toolpath."""
        if not moves:
            return

        # Clear previous actors
        for actor in self.actors.values():
            if actor:
                self.renderer.RemoveActor(actor)
        self.actors = {}

        # Reset move data
        for move_type in self.move_data:
            self.move_data[move_type]["points"] = vtk.vtkPoints()
            self.move_data[move_type]["lines"] = vtk.vtkCellArray()
            self.move_data[move_type]["actor"] = None

        prev_point = None

        for move in moves:
            # Handle tool changes and spindle commands (no coordinates)
            if move.is_tool_change or move.is_spindle_on or move.is_spindle_off:
                continue

            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if prev_point is not None:
                # Add line segment based on move type
                if move.is_rapid:
                    self._add_line_segment(
                        self.move_data["rapid"]["points"],
                        self.move_data["rapid"]["lines"],
                        prev_point,
                        current_point,
                    )
                elif move.is_cutting:
                    self._add_line_segment(
                        self.move_data["cutting"]["points"],
                        self.move_data["cutting"]["lines"],
                        prev_point,
                        current_point,
                    )
                elif move.is_arc:
                    self._add_line_segment(
                        self.move_data["arc"]["points"],
                        self.move_data["arc"]["lines"],
                        prev_point,
                        current_point,
                    )

            prev_point = current_point

        # Create actors for each move type
        for move_type in ["rapid", "cutting", "arc"]:
            if self.move_data[move_type]["points"].GetNumberOfPoints() > 0:
                actor = self._create_actor(
                    self.move_data[move_type]["points"],
                    self.move_data[move_type]["lines"],
                    self.colors[move_type],
                    self.line_widths[move_type],
                )
                self.renderer.AddActor(actor)
                self.actors[move_type] = actor

        # Add axes
        self._add_axes()

        # Reset camera
        self.renderer.ResetCamera()

    def _add_line_segment(self, points, lines, start: tuple, end: tuple) -> None:
        """Add a line segment to the polydata."""
        start_id = points.InsertNextPoint(start)
        end_id = points.InsertNextPoint(end)

        line = self.vtk.vtkLine()
        line.GetPointIds().SetId(0, start_id)
        line.GetPointIds().SetId(1, end_id)
        lines.InsertNextCell(line)

    def _create_actor(self, points, lines, color: tuple, line_width: float):
        """Create a VTK actor from points and lines."""
        polydata = self.vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = self.vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = self.vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)

        return actor

    def _add_axes(self) -> None:
        """Add coordinate axes to the scene."""
        axes = self.vtk.vtkAxesActor()
        axes.SetScale(10.0)

        # Create a transform to position the axes
        transform = self.vtk.vtkTransform()
        transform.Translate(0, 0, 0)
        axes.SetUserTransform(transform)

        self.renderer.AddActor(axes)

    def get_renderer(self):
        """Get the VTK renderer."""
        return self.renderer

    def get_render_window(self):
        """Get the VTK render window."""
        return self.render_window

    def reset_camera(self) -> None:
        """Reset camera to fit all actors."""
        self.renderer.ResetCamera()

    def set_background_color(self, r: float, g: float, b: float) -> None:
        """Set renderer background color."""
        self.renderer.SetBackground(r, g, b)

    def clear_incremental(self) -> None:
        """Clear incremental rendering data."""
        for move_type in self.move_data:
            self.move_data[move_type]["points"] = self.vtk.vtkPoints()
            self.move_data[move_type]["lines"] = self.vtk.vtkCellArray()

            # Remove old actor if exists
            if self.move_data[move_type]["actor"]:
                self.renderer.RemoveActor(self.move_data[move_type]["actor"])
                # Properly cleanup VTK resources
                self.move_data[move_type]["actor"].ReleaseGraphicsResources(self.render_window)
            self.move_data[move_type]["actor"] = None

        self.prev_point = None

    def add_moves_incremental(self, moves: List[GcodeMove]) -> None:
        """Add moves incrementally and update visualization."""
        for move in moves:
            # Skip non-coordinate moves
            if move.is_tool_change or move.is_spindle_on or move.is_spindle_off:
                continue

            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if self.prev_point is not None:
                if move.is_rapid:
                    self._add_line_segment(
                        self.move_data["rapid"]["points"],
                        self.move_data["rapid"]["lines"],
                        self.prev_point,
                        current_point,
                    )
                elif move.is_cutting:
                    self._add_line_segment(
                        self.move_data["cutting"]["points"],
                        self.move_data["cutting"]["lines"],
                        self.prev_point,
                        current_point,
                    )
                elif move.is_arc:
                    self._add_line_segment(
                        self.move_data["arc"]["points"],
                        self.move_data["arc"]["lines"],
                        self.prev_point,
                        current_point,
                    )

            self.prev_point = current_point

        # Update actors
        self._update_incremental_actors()

    def _update_incremental_actors(self) -> None:
        """Update the incremental rendering actors with proper cleanup."""
        for move_type in self.move_data:
            # Proper VTK cleanup sequence
            old_actor = self.move_data[move_type]["actor"]
            if old_actor:
                self.renderer.RemoveActor(old_actor)
                # Clean up the actor's internal resources
                old_actor.ReleaseGraphicsResources(self.render_window)
                del old_actor  # Explicit deletion

            self.move_data[move_type]["actor"] = None

        # Create new actors
        for move_type in ["rapid", "cutting", "arc"]:
            if self.move_data[move_type]["points"].GetNumberOfPoints() > 0:
                actor = self._create_actor(
                    self.move_data[move_type]["points"],
                    self.move_data[move_type]["lines"],
                    self.colors[move_type],
                    self.line_widths[move_type],
                )
                self.renderer.AddActor(actor)
                self.move_data[move_type]["actor"] = actor

    def cleanup(self) -> None:
        """Cleanup all VTK resources before destruction."""
        # Remove all actors
        for move_type in self.move_data:
            if self.move_data[move_type]["actor"]:
                self.renderer.RemoveActor(self.move_data[move_type]["actor"])
                self.move_data[move_type]["actor"].ReleaseGraphicsResources(self.render_window)

        # Clear data structures
        self.move_data.clear()
        self.actors.clear()

        # Clean up renderer and window
        if self.render_window:
            self.render_window.Finalize()
