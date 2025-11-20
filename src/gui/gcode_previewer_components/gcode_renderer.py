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

    def __init__(self) -> None:
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
                "colors": [],
                "actor": None,
            },
            "cutting": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "colors": [],
                "actor": None,
            },
            "arc": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "colors": [],
                "actor": None,
            },
            "tool_change": {
                "points": vtk.vtkPoints(),
                "lines": vtk.vtkCellArray(),
                "colors": [],
                "actor": None,
            },
        }
        self.prev_point = None
        # Counter to throttle how often we rebuild VTK actors during incremental loading
        self._incremental_update_counter = 0
        # Persist per-move-type visibility so UI filters survive re-renders
        self.visibility = {"rapid": True, "cutting": True, "arc": True, "tool_change": True}

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
                    "VTK is required for G-code rendering. Install with: pip install vtk"
                ) from e

    @property
    def vtk(self) -> None:
        """Access VTK module."""
        return self._vtk_module

    def render_toolpath(self, moves: List[GcodeMove], *, fit_camera: bool = False) -> None:
        """Render a list of G-code moves as a 3D toolpath."""
        if not moves:
            return

        # Clear previous actors
        for actor in self.actors.values():
            if actor:
                self.renderer.RemoveActor(actor)
        self.actors = {}

        # Reset move data
        vtk_module = self.vtk
        for move_type, data in self.move_data.items():
            data["points"] = vtk_module.vtkPoints()
            data["lines"] = vtk_module.vtkCellArray()
            data["colors"] = []
            data["actor"] = None

        prev_point = None

        # Precompute cutting count defensively; avoid division by zero and unexpected attributes.
        try:
            total_cutting_segments = sum(
                1
                for m in moves
                if getattr(m, "is_cutting", False)
                and getattr(m, "x", None) is not None
                and getattr(m, "y", None) is not None
                and getattr(m, "z", None) is not None
            )
        except Exception:
            total_cutting_segments = 0
        cutting_index = 0

        for move in moves:
            # Handle tool changes and spindle commands (no coordinates)
            if move.is_tool_change or move.is_spindle_on or move.is_spindle_off:
                continue

            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if prev_point is not None:
                # Add line segment based on move type
                try:
                    if move.is_rapid:
                        self._add_line_segment(
                            self.move_data["rapid"]["points"],
                            self.move_data["rapid"]["lines"],
                            self.move_data["rapid"]["colors"],
                            prev_point,
                            current_point,
                            self.colors["rapid"],
                        )
                    elif move.is_cutting:
                        t = cutting_index / max(1, total_cutting_segments - 1)
                        r = 0.5 * (1 - t)
                        g = 0.5 + 0.5 * t
                        b = 0.5 * (1 - t)
                        gradient_color = (r, g, b)
                        cutting_index += 1

                        self._add_line_segment(
                            self.move_data["cutting"]["points"],
                            self.move_data["cutting"]["lines"],
                            self.move_data["cutting"]["colors"],
                            prev_point,
                            current_point,
                            gradient_color,
                        )
                    elif move.is_arc:
                        self._add_line_segment(
                            self.move_data["arc"]["points"],
                            self.move_data["arc"]["lines"],
                            self.move_data["arc"]["colors"],
                            prev_point,
                            current_point,
                            self.colors["arc"],
                        )
                except Exception:
                    # Skip malformed move entries and continue rendering the rest.
                    pass

            prev_point = current_point

        # Create actors for each move type
        for move_type in ["rapid", "cutting", "arc"]:
            if self.move_data[move_type]["points"].GetNumberOfPoints() > 0:
                actor = self._create_actor(
                    self.move_data[move_type]["points"],
                    self.move_data[move_type]["lines"],
                    self.colors[move_type],
                    self.line_widths[move_type],
                    self.move_data[move_type]["colors"],
                )
                self.renderer.AddActor(actor)
                self.actors[move_type] = actor
                try:
                    actor.SetVisibility(bool(self.visibility.get(move_type, True)))
                except Exception:
                    pass

        # Reset camera only when explicitly requested (initial fit)
        if fit_camera:
            self.renderer.ResetCamera()
            self.renderer.ResetCameraClippingRange()

    def _add_line_segment(self, points, lines, colors, start: tuple, end: tuple, color: tuple) -> None:
        """Add a line segment to the polydata."""
        try:
            start_id = points.InsertNextPoint(start)
            end_id = points.InsertNextPoint(end)

            line = self.vtk.vtkLine()
            line.GetPointIds().SetId(0, start_id)
            line.GetPointIds().SetId(1, end_id)
            lines.InsertNextCell(line)
            colors.append(color)
        except Exception:
            # Ignore invalid geometry
            pass

    def _create_actor(self, points, lines, color: tuple, line_width: float, colors: list) -> None:
        """Create a VTK actor from points and lines."""
        polydata = self.vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = self.vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        # Per-cell coloring if colors were provided
        if colors:
            try:
                color_array = self.vtk.vtkUnsignedCharArray()
                color_array.SetNumberOfComponents(3)
                color_array.SetNumberOfTuples(len(colors))
                for idx, col in enumerate(colors):
                    r, g, b = col
                    color_array.SetTuple3(idx, int(r * 255), int(g * 255), int(b * 255))
                polydata.GetCellData().SetScalars(color_array)
                mapper.SetColorModeToDirectScalars()
            except Exception:
                # If coloring fails, fall back to default mapper color
                pass
        actor = self.vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)

        return actor

    def add_axes(self) -> None:
        """Add coordinate axes to the scene (disabled in favor of corner marker)."""
        return

    def get_renderer(self) -> None:
        """Get the VTK renderer."""
        return self.renderer

    def get_render_window(self) -> None:
        """Get the VTK render window."""
        return self.render_window

    def reset_camera(self) -> None:
        """Reset camera to fit all actors and adjust clipping range."""
        self.renderer.ResetCamera()
        self.renderer.ResetCameraClippingRange()

    def set_background_color(self, r: float, g: float, b: float) -> None:
        """Set renderer background color."""
        self.renderer.SetBackground(r, g, b)

    def clear_incremental(self) -> None:
        """Clear incremental rendering data."""
        for data in self.move_data.values():
            data["points"] = self.vtk.vtkPoints()
            data["lines"] = self.vtk.vtkCellArray()
            data["colors"] = []

            # Remove old actor if exists
            if data["actor"]:
                self.renderer.RemoveActor(data["actor"])
                # Properly cleanup VTK resources
                data["actor"].ReleaseGraphicsResources(self.render_window)
            data["actor"] = None

        self.prev_point = None
        self._incremental_update_counter = 0

    def add_moves_incremental(self, moves: List[GcodeMove]) -> None:
        """Add moves incrementally and update visualization.

        To keep large files responsive, we throttle how often we rebuild VTK
        actors and let the loader thread stream moves in small chunks.
        """
        for move in moves:
            # Skip non-coordinate moves
            if move.is_tool_change or move.is_spindle_on or move.is_spindle_off:
                continue

            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if self.prev_point is not None:
                try:
                    if move.is_rapid:
                        self._add_line_segment(
                            self.move_data["rapid"]["points"],
                            self.move_data["rapid"]["lines"],
                            self.move_data["rapid"]["colors"],
                            self.prev_point,
                            current_point,
                            self.colors["rapid"],
                        )
                    elif move.is_cutting:
                        self._add_line_segment(
                            self.move_data["cutting"]["points"],
                            self.move_data["cutting"]["lines"],
                            self.move_data["cutting"]["colors"],
                            self.prev_point,
                            current_point,
                            self.colors["cutting"],
                        )
                    elif move.is_arc:
                        self._add_line_segment(
                            self.move_data["arc"]["points"],
                            self.move_data["arc"]["lines"],
                            self.move_data["arc"]["colors"],
                            self.prev_point,
                            current_point,
                            self.colors["arc"],
                        )
                except Exception:
                    # Skip malformed move entries and continue rendering the rest.
                    pass

            self.prev_point = current_point

        # Throttle actor rebuilds to avoid UI stalls on very large files
        self._incremental_update_counter += 1
        if self._incremental_update_counter >= 10:
            try:
                self.update_incremental_actors()
            except Exception:
                # Renderer errors should not break loading; skip update when VTK misbehaves.
                pass
            self._incremental_update_counter = 0

    def update_incremental_actors(self) -> None:
        """Update the incremental rendering actors with proper cleanup."""
        for data in self.move_data.values():
            # Proper VTK cleanup sequence
            old_actor = data["actor"]
            if old_actor:
                self.renderer.RemoveActor(old_actor)
                # Clean up the actor's internal resources
                old_actor.ReleaseGraphicsResources(self.render_window)
                del old_actor  # Explicit deletion

            data["actor"] = None

        # Create new actors
        for move_type, data in self.move_data.items():
            if move_type not in ("rapid", "cutting", "arc"):
                continue

            if data["points"].GetNumberOfPoints() > 0:
                actor = self._create_actor(
                    data["points"],
                    data["lines"],
                    self.colors[move_type],
                    self.line_widths[move_type],
                    data["colors"],
                )
                self.renderer.AddActor(actor)
                data["actor"] = actor
                try:
                    actor.SetVisibility(bool(self.visibility.get(move_type, True)))
                except Exception:
                    pass

    def set_move_visibility(self, move_key: str, visible: bool) -> None:
        """Set visibility for a given move group across both full and incremental actors."""
        self.visibility[move_key] = bool(visible)
        target_actor = None
        if move_key in self.actors:
            target_actor = self.actors.get(move_key)
        if target_actor is None and move_key in self.move_data:
            target_actor = self.move_data[move_key].get("actor")

        if target_actor is not None:
            try:
                target_actor.SetVisibility(bool(visible))
            except Exception:
                pass

    def cleanup(self) -> None:
        """Cleanup all VTK resources before destruction."""
        # Remove all actors
        for data in self.move_data.values():
            if data["actor"]:
                self.renderer.RemoveActor(data["actor"])
                data["actor"].ReleaseGraphicsResources(self.render_window)

        # Clear data structures
        self.move_data.clear()
        self.actors.clear()

        # Clean up renderer and window
        if self.render_window:
            self.render_window.Finalize()
