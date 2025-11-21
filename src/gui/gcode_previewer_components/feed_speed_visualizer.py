"""Feed Rate & Spindle Speed Visualizer - Color-code toolpath by feed/speed."""

from typing import List, Tuple
import vtk

from .gcode_parser import GcodeMove


class FeedSpeedVisualizer:
    """Visualizes feed rate and spindle speed as color gradients on toolpath."""

    def __init__(self) -> None:
        """Initialize the visualizer."""
        self.feed_rate_actor = None
        self.spindle_speed_actor = None
        self.current_mode = "feed_rate"  # "feed_rate" or "spindle_speed"

    def create_feed_rate_visualization(self, moves: List[GcodeMove]) -> vtk.vtkActor:
        """
        Create a visualization colored by feed rate.

        Args:
            moves: List of G-code moves

        Returns:
            VTK actor with feed rate coloring
        """
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.SetName("Colors")

        # Get feed rate range
        feed_rates = [m.feed_rate for m in moves if m.feed_rate is not None]
        if not feed_rates:
            return self._create_default_actor(moves)

        min_feed = min(feed_rates)
        max_feed = max(feed_rates)
        feed_range = max_feed - min_feed if max_feed > min_feed else 1.0

        prev_point = None

        for move in moves:
            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if prev_point is not None:
                # Add line segment
                start_id = points.InsertNextPoint(prev_point)
                end_id = points.InsertNextPoint(current_point)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, start_id)
                line.GetPointIds().SetId(1, end_id)
                lines.InsertNextCell(line)

                # Color based on feed rate
                if move.feed_rate is not None:
                    normalized = (move.feed_rate - min_feed) / feed_range
                    r, g, b = self._get_color_for_value(normalized)
                    colors.InsertNextTuple3(r, g, b)
                    colors.InsertNextTuple3(r, g, b)

            prev_point = current_point

        return self._create_colored_actor(points, lines, colors)

    def create_spindle_speed_visualization(
        self, moves: List[GcodeMove]
    ) -> vtk.vtkActor:
        """
        Create a visualization colored by spindle speed.

        Args:
            moves: List of G-code moves

        Returns:
            VTK actor with spindle speed coloring
        """
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.SetName("Colors")

        # Get spindle speed range
        speeds = [m.spindle_speed for m in moves if m.spindle_speed is not None]
        if not speeds:
            return self._create_default_actor(moves)

        min_speed = min(speeds)
        max_speed = max(speeds)
        speed_range = max_speed - min_speed if max_speed > min_speed else 1.0

        prev_point = None

        for move in moves:
            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)

            if prev_point is not None:
                # Add line segment
                start_id = points.InsertNextPoint(prev_point)
                end_id = points.InsertNextPoint(current_point)

                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, start_id)
                line.GetPointIds().SetId(1, end_id)
                lines.InsertNextCell(line)

                # Color based on spindle speed
                if move.spindle_speed is not None:
                    normalized = (move.spindle_speed - min_speed) / speed_range
                    r, g, b = self._get_color_for_value(normalized)
                    colors.InsertNextTuple3(r, g, b)
                    colors.InsertNextTuple3(r, g, b)

            prev_point = current_point

        return self._create_colored_actor(points, lines, colors)

    def _get_color_for_value(self, normalized: float) -> Tuple[int, int, int]:
        """
        Get RGB color for a normalized value (0.0 to 1.0).
        Uses a blue -> cyan -> green -> yellow -> red gradient.
        """
        # Clamp value
        normalized = max(0.0, min(1.0, normalized))

        if normalized < 0.25:
            # Blue to Cyan
            t = normalized / 0.25
            r = 0
            g = int(255 * t)
            b = 255
        elif normalized < 0.5:
            # Cyan to Green
            t = (normalized - 0.25) / 0.25
            r = 0
            g = 255
            b = int(255 * (1 - t))
        elif normalized < 0.75:
            # Green to Yellow
            t = (normalized - 0.5) / 0.25
            r = int(255 * t)
            g = 255
            b = 0
        else:
            # Yellow to Red
            t = (normalized - 0.75) / 0.25
            r = 255
            g = int(255 * (1 - t))
            b = 0

        return (r, g, b)

    def _create_colored_actor(
        self,
        points: vtk.vtkPoints,
        lines: vtk.vtkCellArray,
        colors: vtk.vtkUnsignedCharArray,
    ) -> vtk.vtkActor:
        """Create a VTK actor with colored lines."""
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)
        polydata.GetPointData().SetScalars(colors)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        mapper.SetScalarModeToUsePointData()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(3.0)

        return actor

    def _create_default_actor(self, moves: List[GcodeMove]) -> vtk.vtkActor:
        """Create a default white actor if no data available."""
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()

        prev_point = None
        for move in moves:
            if move.x is None or move.y is None or move.z is None:
                continue

            current_point = (move.x, move.y, move.z)
            if prev_point is not None:
                start_id = points.InsertNextPoint(prev_point)
                end_id = points.InsertNextPoint(current_point)
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, start_id)
                line.GetPointIds().SetId(1, end_id)
                lines.InsertNextCell(line)

            prev_point = current_point

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        actor.GetProperty().SetLineWidth(2.0)

        return actor
