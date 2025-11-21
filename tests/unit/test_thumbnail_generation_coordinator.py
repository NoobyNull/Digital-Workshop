"""
Unit tests for ThumbnailGenerationCoordinator.

Tests the coordinator's ability to manage thumbnail generation with a dedicated window.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.gui.thumbnail_generation_coordinator import ThumbnailGenerationCoordinator
from src.gui.progress_window.thumbnail_generation_window import (
    ThumbnailGenerationWindow,
)


class TestThumbnailGenerationCoordinator(unittest.TestCase):
    """Test ThumbnailGenerationCoordinator."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = ThumbnailGenerationCoordinator()
        self.test_files = [
            ("model1.stl", "hash1"),
            ("model2.stl", "hash2"),
            ("model3.stl", "hash3"),
        ]

    def tearDown(self):
        """Clean up after tests."""
        if self.coordinator.window:
            self.coordinator.window.close()
        if self.coordinator.worker:
            self.coordinator.worker.quit()
            self.coordinator.worker.wait()

    def test_coordinator_initialization(self):
        """Test coordinator initializes correctly."""
        self.assertIsNone(self.coordinator.worker)
        self.assertIsNone(self.coordinator.window)
        self.assertIsNotNone(self.coordinator.logger)

    def test_generate_thumbnails_creates_window(self):
        """Test that generate_thumbnails creates a window."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            # Verify window was created
            self.assertIsNotNone(self.coordinator.window)
            self.assertIsInstance(self.coordinator.window, ThumbnailGenerationWindow)

    def test_generate_thumbnails_creates_worker(self):
        """Test that generate_thumbnails creates a worker."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            # Verify worker was created with correct parameters
            mock_worker_class.assert_called_once()
            call_kwargs = mock_worker_class.call_args[1]
            self.assertEqual(call_kwargs["file_info_list"], self.test_files)
            self.assertEqual(call_kwargs["background"], "#FFFFFF")
            self.assertEqual(call_kwargs["material"], "default")

    def test_generate_thumbnails_empty_list(self):
        """Test that generate_thumbnails handles empty file list."""
        self.coordinator.generate_thumbnails(file_info_list=[])

        # Should not create window or worker
        self.assertIsNone(self.coordinator.window)
        self.assertIsNone(self.coordinator.worker)

    def test_is_running_when_worker_active(self):
        """Test is_running returns True when worker is active."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker.isRunning.return_value = True
            mock_worker_class.return_value = mock_worker

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            self.assertTrue(self.coordinator.is_running())

    def test_is_running_when_worker_inactive(self):
        """Test is_running returns False when worker is inactive."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker.isRunning.return_value = False
            mock_worker_class.return_value = mock_worker

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            self.assertFalse(self.coordinator.is_running())

    def test_stop_calls_worker_stop(self):
        """Test that stop() calls worker.stop()."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            self.coordinator.stop()
            mock_worker.stop.assert_called_once()

    def test_signals_emitted_on_generation_started(self):
        """Test that generation_started signal is emitted."""
        with patch(
            "src.gui.thumbnail_generation_coordinator.ThumbnailGenerationWorker"
        ) as mock_worker_class:
            mock_worker = MagicMock()
            mock_worker_class.return_value = mock_worker

            signal_emitted = False

            def on_started():
                nonlocal signal_emitted
                signal_emitted = True

            self.coordinator.generation_started.connect(on_started)

            self.coordinator.generate_thumbnails(
                file_info_list=self.test_files,
                background="#FFFFFF",
                material="default",
            )

            self.assertTrue(signal_emitted)


if __name__ == "__main__":
    unittest.main()
