"""G-code Renderer - VTK-based 3D visualization of G-code toolpaths."""

from typing import List, Optional, Dict, TYPE_CHECKING, Tuple
from .gcode_parser import GcodeMove

# Type hints only import
if TYPE_CHECKING:
    import vtk as VtkModule


Color = Tuple[float, float, float]


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

        # Persistent actors
        self.actors: Dict[str, vtk.vtkActor] = {}
        self.bounds = None

        # Full-path state for progressive coloring
        self._cut_polydata = None
        self._cut_colors = None
        self._cut_segment_map: List[int] = []  # segment index -> move index
        self._full_moves: List[GcodeMove] = []
        self._tool_actor: Optional[vtk.vtkActor] = None
        self._tool_radius = 0.0
        self._last_frame_index = -1

        # For incremental rendering during streaming load
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
        self.visibility = {
            "rapid": True,
            "cutting": True,
            "arc": True,
            "tool_change": True,
            "ahead": True,
        }

        # Color scheme for different move types
        self.colors: Dict[str, Color] = {
            "rapid": (1.0, 0.5, 0.0),  # Orange - fast moves
            "cutting": (0.0, 0.8, 0.4),  # Green - cutting moves
            "ahead": (0.35, 0.35, 0.7),  # Cool blue - yet-to-cut
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

    # ------------------------------------------------------------------
    # Progressive toolpath (no per-frame rebuild)
    # ------------------------------------------------------------------
    def prepare_full_path(self, moves: List[GcodeMove], *, fit_camera: bool = False) -> None:
        """Build the full toolpath once and keep it for fast progressive updates."""
        if not moves:
            self.clear_full_path()
            return

        self._full_moves = list(moves)
        self._cut_segment_map = []

        vtk_module = self.vtk
        cut_points = vtk_module.vtkPoints()
        cut_lines = vtk_module.vtkCellArray()

        rapid_points = vtk_module.vtkPoints()
        rapid_lines = vtk_module.vtkCellArray()
        arc_points = vtk_module.vtkPoints()
        arc_lines = vtk_module.vtkCellArray()

        # RGBA colors for cutting segments; ahead segments start as "ahead"
        self._cut_colors = vtk_module.vtkUnsignedCharArray()
        self._cut_colors.SetNumberOfComponents(4)

        prev_point = None
        bounds = [float("inf"), float("-inf"), float("inf"), float("-inf"), float("inf"), float("-inf")]

        def _track_bounds(x: float, y: float, z: float) -> None:
            bounds[0] = min(bounds[0], x)
            bounds[1] = max(bounds[1], x)
            bounds[2] = min(bounds[2], y)
            bounds[3] = max(bounds[3], y)
            bounds[4] = min(bounds[4], z)
            bounds[5] = max(bounds[5], z)

        for move_index, move in enumerate(moves):
            if move.x is None or move.y is None or move.z is None:
                continue
            current_point = (move.x, move.y, move.z)
            _track_bounds(*current_point)

            if prev_point is not None:
                if move.is_rapid:
                    self._add_line_segment(rapid_points, rapid_lines, [], prev_point, current_point, None)
                elif move.is_cutting or move.is_arc:
                    self._cut_segment_map.append(move_index)
                    self._add_line_segment(cut_points, cut_lines, [], prev_point, current_point, None)
                else:
                    # Treat unclassified linear motions as cutting for visibility
                    self._cut_segment_map.append(move_index)
                    self._add_line_segment(cut_points, cut_lines, [], prev_point, current_point, None)
            prev_point = current_point

        # Build colors for cutting polydata (ahead by default)
        segment_count = len(self._cut_segment_map)
        if self._cut_colors is not None and segment_count:
            self._cut_colors.SetNumberOfTuples(segment_count)
            ahead_color = self._rgba255(self.colors["ahead"], alpha=255)
            for idx in range(segment_count):
                self._cut_colors.SetTuple4(idx, *ahead_color)

        # Clear old actors and build fresh
        self.clear_full_path()
        self.actors = {}

        # Cutting actor
        if cut_points.GetNumberOfPoints() > 0:
            self._cut_polydata = vtk_module.vtkPolyData()
            self._cut_polydata.SetPoints(cut_points)
            self._cut_polydata.SetLines(cut_lines)
            if self._cut_colors is not None and self._cut_colors.GetNumberOfTuples() > 0:
                self._cut_polydata.GetCellData().SetScalars(self._cut_colors)

            cut_actor = self._create_actor(
                self._cut_polydata,
                self.colors["cutting"],
                self.line_widths["cutting"],
                use_cell_scalars=True,
            )
            self.renderer.AddActor(cut_actor)
            self.actors["cutting"] = cut_actor

        # Rapid actor
        if rapid_points.GetNumberOfPoints() > 0:
            rapid_poly = vtk_module.vtkPolyData()
            rapid_poly.SetPoints(rapid_points)
            rapid_poly.SetLines(rapid_lines)
            rapid_actor = self._create_actor(
                rapid_poly,
                self.colors["rapid"],
                self.line_widths["rapid"],
                use_cell_scalars=False,
            )
            self.renderer.AddActor(rapid_actor)
            self.actors["rapid"] = rapid_actor

        # Arc actor (kept for clarity even though arcs are included as cutting)
        if arc_points.GetNumberOfPoints() > 0:
            arc_poly = vtk_module.vtkPolyData()
            arc_poly.SetPoints(arc_points)
            arc_poly.SetLines(arc_lines)
            arc_actor = self._create_actor(
                arc_poly,
                self.colors["arc"],
                self.line_widths["arc"],
                use_cell_scalars=False,
            )
            self.renderer.AddActor(arc_actor)
            self.actors["arc"] = arc_actor

        # Tool indicator actor sized from bounds
        if all(b != float("inf") and b != float("-inf") for b in bounds):
            max_extent = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
            self._tool_radius = max(0.5, max_extent * 0.01)
            center = (
                0.5 * (bounds[0] + bounds[1]),
                0.5 * (bounds[2] + bounds[3]),
                0.5 * (bounds[4] + bounds[5]),
            )
            self._ensure_tool_actor(center)

        # Apply visibility flags
        for move_type, actor in self.actors.items():
            actor.SetVisibility(bool(self.visibility.get(move_type, True)))

        # Fit camera only when explicitly requested
        if fit_camera:
            self.renderer.ResetCamera()
            self.renderer.ResetCameraClippingRange()

    def update_cut_progress(self, frame_index: int) -> None:
        """Update cut vs ahead colors without rebuilding geometry."""
        if not self._cut_segment_map or self._cut_colors is None:
            return

        cut_limit = -1
        for seg_idx, move_idx in enumerate(self._cut_segment_map):
            if move_idx <= frame_index:
                cut_limit = seg_idx
            else:
                break

        cut_color = self._rgba255(
            self.colors["cutting"], alpha=255 if self.visibility.get("cutting", True) else 0
        )
        ahead_color = self._rgba255(
            self.colors["ahead"], alpha=255 if self.visibility.get("ahead", True) else 0
        )

        for seg_idx in range(self._cut_colors.GetNumberOfTuples()):
            if seg_idx <= cut_limit:
                self._cut_colors.SetTuple4(seg_idx, *cut_color)
            else:
                self._cut_colors.SetTuple4(seg_idx, *ahead_color)

        self._cut_colors.Modified()
        if self._cut_polydata is not None:
            self._cut_polydata.Modified()
        self._last_frame_index = frame_index

    def update_toolhead_position(self, move: Optional[GcodeMove]) -> None:
        """Move the tool indicator to the current move position."""
        if move is None or move.x is None or move.y is None or move.z is None:
            return
        center = (move.x, move.y, move.z)
        self._ensure_tool_actor(center)

    def set_cut_colors(self, *, cut: Optional[Color] = None, ahead: Optional[Color] = None) -> None:
        """Update stored colors and refresh the current cut mask."""
        if cut:
            self.colors["cutting"] = cut
        if ahead:
            self.colors["ahead"] = ahead
        self.update_cut_progress(self._last_frame_index if self._last_frame_index >= 0 else -1)

    def clear_full_path(self) -> None:
        """Remove the persistent path actors and tool indicator."""
        for actor in self.actors.values():
            if actor:
                self.renderer.RemoveActor(actor)
                actor.ReleaseGraphicsResources(self.render_window)
        self.actors = {}
        if self._tool_actor:
            self.renderer.RemoveActor(self._tool_actor)
            self._tool_actor.ReleaseGraphicsResources(self.render_window)
            self._tool_actor = None

        self._cut_polydata = None
        self._cut_colors = None
        self._cut_segment_map = []
        self._full_moves = []
        self._last_frame_index = -1

    # ------------------------------------------------------------------
    # Legacy entry points (kept for layer toggles & static previews)
    # ------------------------------------------------------------------
    def render_toolpath(self, moves: List[GcodeMove], *, fit_camera: bool = False) -> None:
        """Render a list of G-code moves as a 3D toolpath."""
        self.prepare_full_path(moves, fit_camera=fit_camera)
        # Show the path as fully cut for static renders
        self.update_cut_progress(len(moves))

    # ------------------------------------------------------------------
    # Incremental rendering used during stream loading
    # ------------------------------------------------------------------
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
                    elif move.is_cutting or move.is_arc:
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
                    (data["points"], data["lines"]),
                    self.colors[move_type],
                    self.line_widths[move_type],
                    self._build_colors_array(data["colors"]),
                    use_cell_scalars=bool(data["colors"]),
                )
                self.renderer.AddActor(actor)
                data["actor"] = actor
                try:
                    actor.SetVisibility(bool(self.visibility.get(move_type, True)))
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _add_line_segment(
        self, points, lines, colors, start: tuple, end: tuple, color: Optional[tuple]
    ) -> None:
        """Add a line segment to the polydata."""
        try:
            start_id = points.InsertNextPoint(start)
            end_id = points.InsertNextPoint(end)

            line = self.vtk.vtkLine()
            line.GetPointIds().SetId(0, start_id)
            line.GetPointIds().SetId(1, end_id)
            lines.InsertNextCell(line)
            if color is not None:
                colors.append(color)
        except Exception:
            # Ignore invalid geometry
            pass

    def _create_actor(
        self, geometry, color: Color, line_width: float, colors_array=None, use_cell_scalars: bool = False
    ):
        """Create a VTK actor from either a polydata or (points, lines) tuple."""
        if hasattr(geometry, "GetClassName"):
            polydata = geometry
        elif isinstance(geometry, tuple) and len(geometry) == 2:
            points, lines = geometry
            polydata = self.vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetLines(lines)
        else:
            raise ValueError("Unsupported geometry passed to _create_actor")

        mapper = self.vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        mapper.SetScalarModeToUseCellData()

        if colors_array is not None:
            try:
                polydata.GetCellData().SetScalars(colors_array)
                mapper.SetColorModeToDirectScalars()
                mapper.ScalarVisibilityOn()
                use_cell_scalars = True
            except Exception:
                use_cell_scalars = False

        actor = self.vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        if use_cell_scalars:
            try:
                actor.GetProperty().SetOpacity(1.0)
            except Exception:
                pass

        return actor

    def _build_colors_array(self, colors: list):
        """Build a VTK color array from a list of RGB tuples."""
        if not colors:
            return None
        array = self.vtk.vtkUnsignedCharArray()
        array.SetNumberOfComponents(4)
        array.SetNumberOfTuples(len(colors))
        for idx, col in enumerate(colors):
            r, g, b = col[:3]
            array.SetTuple4(idx, int(r * 255), int(g * 255), int(b * 255), 255)
        return array

    def _ensure_tool_actor(self, center: tuple) -> None:
        """Create a small sphere that follows the toolhead."""
        vtk_module = self.vtk
        if self._tool_actor is None:
            sphere = vtk_module.vtkSphereSource()
            sphere.SetRadius(max(0.5, self._tool_radius or 0.5))

            mapper = vtk_module.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())

            actor = vtk_module.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1.0, 1.0, 0.2)
            actor.GetProperty().SetOpacity(0.9)
            self.renderer.AddActor(actor)
            self._tool_actor = actor

        try:
            self._tool_actor.SetPosition(*center)
            self._tool_actor.SetVisibility(True)
        except Exception:
            pass

    def _rgba255(self, color: Color, *, alpha: int = 255) -> tuple:
        """Helper to convert float colors (0-1) to 0-255 RGBA tuple."""
        r, g, b = color
        return (int(r * 255), int(g * 255), int(b * 255), int(alpha))

    # ------------------------------------------------------------------
    # Standard controls
    # ------------------------------------------------------------------
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

        # Ahead visibility is driven by alpha in the color mask
        if move_key in ("ahead", "cutting"):
            self.update_cut_progress(self._last_frame_index if self._last_frame_index >= 0 else -1)

    def cleanup(self) -> None:
        """Cleanup all VTK resources before destruction."""
        # Remove all actors
        for data in self.move_data.values():
            if data["actor"]:
                self.renderer.RemoveActor(data["actor"])
                data["actor"].ReleaseGraphicsResources(self.render_window)

        for actor in self.actors.values():
            if actor:
                self.renderer.RemoveActor(actor)
                actor.ReleaseGraphicsResources(self.render_window)

        if self._tool_actor:
            self.renderer.RemoveActor(self._tool_actor)
            self._tool_actor.ReleaseGraphicsResources(self.render_window)

        # Clear data structures
        self.move_data.clear()
        self.actors.clear()

        # Clean up renderer and window
        if self.render_window:
            self.render_window.Finalize()
