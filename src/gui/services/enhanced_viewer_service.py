"""
Enhanced viewer service implementation with progress tracking, cancellation support, and performance optimization.
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import Signal, QThread

from src.core.logging_config import get_logger
from src.core.performance_monitor import get_performance_monitor
from src.core.model_cache import get_model_cache
from src.core.data_structures import Model

from .gui_service_interfaces import (
    IEnhancedViewerService,
    IViewerUIService,
    ProgressInfo,
    UIState,
)
from ..viewer_3d.viewer_widget_facade import Viewer3DWidget


class ModelLoadingWorker(QThread):
    """Worker thread for loading models asynchronously."""

    # Signals
    progress_updated = Signal(object)  # ProgressInfo
    loading_completed = Signal(bool, str)  # success, model_info
    error_occurred = Signal(str, str)  # error_type, message

    def __init__(
        self,
        file_path: Path,
        viewer_widget: Viewer3DWidget,
        cancellation_check: Callable[[], bool],
    ):
        """
        Initialize model loading worker.

        Args:
            file_path: Path to the model file
            viewer_widget: Viewer widget to load model into
            cancellation_check: Function to check for cancellation
        """
        super().__init__()
        self.file_path = file_path
        self.viewer_widget = viewer_widget
        self.cancellation_check = cancellation_check
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Run the model loading operation."""
        try:
            self.logger.info("Starting async model loading: %s", self.file_path)

            # Check for cancellation
            if self.cancellation_check():
                self.logger.info("Model loading cancelled before starting")
                return

            # Simulate progress steps for different file sizes
            file_size = self.file_path.stat().st_size if self.file_path.exists() else 0
            estimated_steps = self._calculate_loading_steps(file_size)

            for step in range(estimated_steps):
                # Check for cancellation
                if self.cancellation_check():
                    self.logger.info("Model loading cancelled during process")
                    return

                # Emit progress update
                progress = ProgressInfo(
                    step,
                    estimated_steps,
                    f"Loading model... ({step}/{estimated_steps})",
                )
                self.progress_updated.emit(progress)

                # Simulate work (in real implementation, this would be actual file parsing)
                time.sleep(0.1)  # Small delay to show progress

            # Final step - actually load the model
            if self.cancellation_check():
                return

            # Create a dummy model for now (in real implementation, would parse actual file)
            model = self._create_dummy_model()

            if model:
                # Load into viewer
                success = self.viewer_widget.load_model(model)

                if success:
                    model_info = {
                        "filename": (
                            model.filename if hasattr(model, "filename") else self.file_path.name
                        ),
                        "file_size": file_size,
                        "triangle_count": (
                            getattr(model, "stats", {}).triangle_count
                            if hasattr(model, "stats")
                            else 0
                        ),
                    }
                    self.loading_completed.emit(True, str(model_info))
                    self.logger.info("Model loading completed successfully")
                else:
                    self.error_occurred.emit("LOADING_ERROR", "Failed to load model into viewer")
            else:
                self.error_occurred.emit("PARSING_ERROR", "Failed to parse model file")

        except Exception as e:
            self.logger.error("Error during model loading: %s", e, exc_info=True)
            self.error_occurred.emit("GENERIC_ERROR", str(e))

    def _calculate_loading_steps(self, file_size: int) -> int:
        """Calculate number of progress steps based on file size."""
        if file_size < 1024 * 1024:  # < 1MB
            return 5
        elif file_size < 50 * 1024 * 1024:  # < 50MB
            return 10
        elif file_size < 200 * 1024 * 1024:  # < 200MB
            return 20
        else:
            return 30

    def _create_dummy_model(self) -> Optional[Model]:
        """Create a dummy model for testing (replace with actual parsing)."""
        try:
            # Create a simple model structure
            class DummyModel:
                def __init__(self):
                    self.filename = (
                        self.file_path.name if hasattr(self, "file_path") else "model.stl"
                    )

                class Stats:
                    triangle_count = 1000
                    format_type = "STL"

                stats = Stats()

            model = DummyModel()
            return model
        except Exception as e:
            self.logger.error("Failed to create dummy model: %s", e)
            return None


class EnhancedViewerService(IEnhancedViewerService):
    """Enhanced viewer service with async loading, progress tracking, and performance optimization."""

    def __init__(self, viewer_widget: Viewer3DWidget, ui_service: IViewerUIService):
        """
        Initialize enhanced viewer service.

        Args:
            viewer_widget: The 3D viewer widget
            ui_service: UI service for progress and state management
        """
        super().__init__()
        self.viewer_widget = viewer_widget
        self.ui_service = ui_service
        self.logger = get_logger(__name__)

        # Performance settings
        self.performance_monitor = get_performance_monitor()
        self.model_cache = get_model_cache()
        self.current_loading_worker: Optional[ModelLoadingWorker] = None
        self.cancellation_requested = False
        self.target_fps = 30
        self.vsync_enabled = True
        self.performance_mode = "balanced"

        # Performance optimization thresholds
        self._setup_performance_thresholds()

        self.logger.info("Enhanced viewer service initialized")

    def _setup_performance_thresholds(self) -> None:
        """Setup performance optimization thresholds based on hardware."""
        perf_profile = self.performance_monitor.get_performance_profile()
        self.max_triangles_for_full_quality = perf_profile.max_triangles_for_full_quality
        self.adaptive_quality = perf_profile.adaptive_quality_enabled

        # Set adaptive FPS based on hardware
        if perf_profile.gpu_score > 80:
            self.target_fps = 60
            self.performance_mode = "high"
        elif perf_profile.gpu_score > 50:
            self.target_fps = 30
            self.performance_mode = "balanced"
        else:
            self.target_fps = 24
            self.performance_mode = "performance"

        self.logger.info(
            f"Performance mode: {self.performance_mode}, target FPS: {self.target_fps}"
        )

    def load_model_async(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
        cancellation_token: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Load a 3D model asynchronously with progress tracking."""
        try:
            # Cancel any existing loading
            if self.current_loading_worker and self.current_loading_worker.isRunning():
                self.cancel_loading()

            # Validate file
            if not file_path.exists():
                self.ui_service.show_error("File Error", f"File not found: {file_path}")
                return False

            # Check file size and estimate loading time
            file_size = file_path.stat().st_size
            if file_size > 500 * 1024 * 1024:  # 500MB
                self.ui_service.show_warning(
                    "Large File",
                    "This is a large file and may take several minutes to load.",
                )

            # Reset cancellation flag
            self.cancellation_requested = False

            # Create cancellation token
            def cancellation_check():
                return self.cancellation_requested or (cancellation_token and cancellation_token())

            # Create and start loading worker
            self.current_loading_worker = ModelLoadingWorker(
                file_path, self.viewer_widget, cancellation_check
            )

            # Connect signals
            self.current_loading_worker.progress_updated.connect(self._on_loading_progress)
            self.current_loading_worker.loading_completed.connect(self._on_loading_completed)
            self.current_loading_worker.error_occurred.connect(self._on_loading_error)

            # Set UI state
            self.ui_service.set_ui_state(UIState.LOADING, "Loading model...")
            self.ui_service.enable_cancellation(True)

            # Start loading
            self.current_loading_worker.start()

            self.logger.info("Started async model loading: %s", file_path)
            return True

        except Exception as e:
            self.logger.error("Failed to start model loading: %s", e, exc_info=True)
            self.ui_service.show_error("Loading Error", f"Failed to start loading: {e}")
            return False

    def _on_loading_progress(self, progress: ProgressInfo) -> None:
        """Handle loading progress updates."""
        try:
            self.ui_service.show_progress(progress)

            # Update UI with progress message
            if progress.message:
                self.ui_service.set_ui_state(UIState.LOADING, progress.message)

        except Exception as e:
            self.logger.error("Error handling loading progress: %s", e)

    def _on_loading_completed(self, success: bool, model_info: str) -> None:
        """Handle loading completion."""
        try:
            self.ui_service.hide_progress()
            self.ui_service.enable_cancellation(False)

            if success:
                self.ui_service.set_ui_state(UIState.READY, "Model loaded successfully")
                self.ui_service.show_info("Success", f"Model loaded successfully!\n{model_info}")
                self.logger.info("Model loading completed successfully")
            else:
                self.ui_service.set_ui_state(UIState.ERROR, "Failed to load model")

        except Exception as e:
            self.logger.error("Error handling loading completion: %s", e)
        finally:
            self.current_loading_worker = None

    def _on_loading_error(self, error_type: str, message: str) -> None:
        """Handle loading errors."""
        try:
            self.ui_service.hide_progress()
            self.ui_service.enable_cancellation(False)
            self.ui_service.set_ui_state(UIState.ERROR, "Loading failed")

            # Show user-friendly error message
            user_message = self._get_user_friendly_error_message(error_type, message)
            self.ui_service.show_error("Loading Error", user_message, message)

            self.logger.error("Model loading failed (%s): {message}", error_type)

        except Exception as e:
            self.logger.error("Error handling loading error: %s", e)
        finally:
            self.current_loading_worker = None

    def _get_user_friendly_error_message(self, error_type: str, message: str) -> str:
        """Convert technical error messages to user-friendly versions."""
        error_messages = {
            "FILE_NOT_FOUND": "The specified file could not be found. Please check the file path.",
            "INVALID_FORMAT": "The file format is not supported. Please use STL, OBJ, or STEP files.",
            "CORRUPTED_FILE": "The file appears to be corrupted and cannot be read.",
            "MEMORY_ERROR": "The file is too large to load in available memory.",
            "LOADING_ERROR": "An error occurred while loading the model into the viewer.",
            "PARSING_ERROR": "The file format could not be parsed correctly.",
        }

        return error_messages.get(
            error_type, f"An error occurred while loading the file: {message}"
        )

    def cancel_loading(self) -> None:
        """Cancel current model loading operation."""
        try:
            if self.current_loading_worker and self.current_loading_worker.isRunning():
                self.cancellation_requested = True
                self.current_loading_worker.terminate()
                self.current_loading_worker.wait(3000)  # Wait up to 3 seconds

                if self.current_loading_worker.isRunning():
                    self.current_loading_worker.kill()
                    self.current_loading_worker.wait()

                self.ui_service.hide_progress()
                self.ui_service.enable_cancellation(False)
                self.ui_service.set_ui_state(UIState.READY, "Loading cancelled")

                self.logger.info("Model loading cancelled by user")

        except Exception as e:
            self.logger.error("Error cancelling loading: %s", e)
        finally:
            self.current_loading_worker = None
            self.cancellation_requested = False

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get viewer performance statistics."""
        try:
            stats = {
                "target_fps": self.target_fps,
                "vsync_enabled": self.vsync_enabled,
                "performance_mode": self.performance_mode,
                "adaptive_quality": self.adaptive_quality,
                "max_triangles_full_quality": self.max_triangles_for_full_quality,
                "loading_worker_active": self.current_loading_worker is not None
                and self.current_loading_worker.isRunning(),
                "current_model_triangles": 0,  # Would get from actual model
            }

            # Add viewer-specific stats if available
            if hasattr(self.viewer_widget, "perf_tracker"):
                viewer_stats = self.viewer_widget.perf_tracker.get_latest_stats()
                stats.update(viewer_stats)

            return stats

        except Exception as e:
            self.logger.error("Error getting performance stats: %s", e)
            return {"error": str(e)}

    def set_performance_mode(self, mode: str) -> None:
        """Set performance mode (quality vs speed tradeoff)."""
        valid_modes = ["high", "balanced", "performance"]
        if mode not in valid_modes:
            self.logger.warning("Invalid performance mode: %s", mode)
            return

        self.performance_mode = mode

        # Adjust settings based on mode
        if mode == "high":
            self.target_fps = 60
            self.adaptive_quality = False
        elif mode == "balanced":
            self.target_fps = 30
            self.adaptive_quality = True
        else:  # performance
            self.target_fps = 24
            self.adaptive_quality = True

        self.logger.info("Performance mode set to: %s", mode)

    def enable_vsync(self, enabled: bool) -> None:
        """Enable or disable VSync for tear-free rendering."""
        self.vsync_enabled = enabled

        # Apply VSync setting to VTK render window
        try:
            if hasattr(self.viewer_widget, "render_window"):
                if enabled:
                    # VTK VSync settings would be applied here
                    self.logger.debug("VSync enabled")
                else:
                    self.logger.debug("VSync disabled")
        except Exception as e:
            self.logger.error("Error applying VSync setting: %s", e)

    def set_target_fps(self, fps: int) -> None:
        """Set target frame rate."""
        if fps < 15 or fps > 120:
            self.logger.warning("Target FPS %s is outside recommended range (15-120)", fps)
            return

        self.target_fps = fps
        self.logger.info("Target FPS set to: %s", fps)

    def optimize_for_model_size(self, triangle_count: int) -> None:
        """Optimize rendering settings based on model complexity."""
        try:
            if triangle_count > 1000000:  # > 1M triangles
                self.performance_mode = "performance"
                self.target_fps = 24
                self.logger.info("Optimized for high-poly model")
            elif triangle_count > 100000:  # > 100K triangles
                self.performance_mode = "balanced"
                self.target_fps = 30
                self.logger.info("Optimized for medium-poly model")
            else:
                self.performance_mode = "high"
                self.target_fps = 60
                self.logger.info("Optimized for low-poly model")

        except Exception as e:
            self.logger.error("Error optimizing for model size: %s", e)
