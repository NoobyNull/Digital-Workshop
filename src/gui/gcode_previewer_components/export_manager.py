"""Export Manager - Export toolpath visualizations to images and videos."""

from pathlib import Path
from typing import Optional
import vtk
from vtk.util import numpy_support
import numpy as np

try:
    import cv2

    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class ExportManager:
    """Manages export of VTK visualizations to images and videos."""

    def __init__(self):
        """Initialize the export manager."""
        self.render_window: Optional[vtk.vtkRenderWindow] = None

    def set_render_window(self, render_window: vtk.vtkRenderWindow) -> None:
        """Set the render window to export from."""
        self.render_window = render_window

    def export_screenshot(self, filepath: str, width: int = 1920, height: int = 1080) -> bool:
        """
        Export a screenshot of the current view.

        Args:
            filepath: Output file path
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            True if successful, False otherwise
        """
        if not self.render_window:
            return False

        try:
            # Set window size
            self.render_window.SetSize(width, height)
            self.render_window.Render()

            # Create image exporter
            exporter = vtk.vtkWindowToImageFilter()
            exporter.SetInput(self.render_window)
            exporter.Update()

            # Write to file
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(filepath)
            writer.SetInputConnection(exporter.GetOutputPort())
            writer.Write()

            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            print(f"Failed to export screenshot: {e}")
            return False

    def export_video(
        self,
        filepath: str,
        frames: list,
        fps: int = 30,
        width: int = 1280,
        height: int = 720,
    ) -> bool:
        """
        Export animation frames as a video.

        Args:
            filepath: Output file path (.mp4, .avi, etc.)
            frames: List of numpy arrays (frames)
            fps: Frames per second
            width: Video width
            height: Video height

        Returns:
            True if successful, False otherwise
        """
        if not HAS_OPENCV:
            print("OpenCV not installed. Cannot export video.")
            return False

        try:
            # Determine codec based on file extension
            ext = Path(filepath).suffix.lower()
            if ext == ".mp4":
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            elif ext == ".avi":
                fourcc = cv2.VideoWriter_fourcc(*"XVID")
            else:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")

            # Create video writer
            out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))

            if not out.isOpened():
                print("Failed to open video writer")
                return False

            # Write frames
            for frame in frames:
                # Ensure frame is the right size and format
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))

                # Convert RGB to BGR for OpenCV
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                out.write(frame.astype(np.uint8))

            out.release()
            return True
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            print(f"Failed to export video: {e}")
            return False

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture current render window as numpy array.

        Returns:
            Numpy array of the rendered image, or None if failed
        """
        if not self.render_window:
            return None

        try:
            # Render current view
            self.render_window.Render()

            # Capture to image
            exporter = vtk.vtkWindowToImageFilter()
            exporter.SetInput(self.render_window)
            exporter.Update()

            # Convert to numpy array
            image_data = exporter.GetOutput()
            width, height, _ = image_data.GetDimensions()

            # Get pixel data
            vtk_array = image_data.GetPointData().GetScalars()
            numpy_array = numpy_support.vtk_to_numpy(vtk_array)

            # Reshape to image format
            numpy_array = numpy_array.reshape((height, width, 3))

            return numpy_array
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            print(f"Failed to capture frame: {e}")
            return None

    def get_supported_video_formats(self) -> list:
        """Get list of supported video formats."""
        if HAS_OPENCV:
            return [".mp4", ".avi", ".mov", ".mkv"]
        return []

    def is_video_export_available(self) -> bool:
        """Check if video export is available."""
        return HAS_OPENCV
