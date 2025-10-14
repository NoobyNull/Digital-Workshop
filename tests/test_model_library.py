"""
Tests for the model library widget.

This module provides comprehensive tests for the model library interface,
including UI functionality, database integration, and performance testing.
"""

import gc
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import List

# Add src directory to path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from PySide6.QtCore import Qt, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from core.database_manager import get_database_manager
from gui.model_library import ModelLibraryWidget, ViewMode, ModelLoadWorker
from parsers.stl_parser import STLParser


class TestModelLibraryWidget(unittest.TestCase):
    """Test cases for the ModelLibraryWidget class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Create QApplication if it doesn't exist
        if not QCoreApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QCoreApplication.instance()
        
        # Create temporary database for testing
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, "test_3dmm.db")
        cls.db_manager = get_database_manager(cls.test_db_path)
        
        # Create test STL file
        cls.test_stl_path = os.path.join(cls.temp_dir, "test_cube.stl")
        cls._create_test_stl_file(cls.test_stl_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Close database connection
        cls.db_manager.close()
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def setUp(self):
        """Set up before each test."""
        # Create widget for testing
        self.widget = ModelLibraryWidget()
        
        # Process any pending events
        QTest.qWait(100)
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up widget
        if hasattr(self, 'widget'):
            self.widget.cleanup()
            self.widget.deleteLater()
        
        # Process any pending events
        QTest.qWait(100)
        
        # Force garbage collection
        gc.collect()
    
    @classmethod
    def _create_test_stl_file(cls, file_path: str) -> None:
        """Create a simple test STL file."""
        # Simple ASCII STL cube
        stl_content = """solid test_cube
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 1.0 1.0 0.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 1.0 0.0
      vertex 0.0 1.0 0.0
    endloop
  endfacet
endsolid test_cube
"""
        with open(file_path, 'w') as f:
            f.write(stl_content)
    
    def test_widget_initialization(self) -> None:
        """Test that the widget initializes correctly."""
        # Check that widget was created
        self.assertIsNotNone(self.widget)
        
        # Check that components exist
        self.assertIsNotNone(self.widget.list_view)
        self.assertIsNotNone(self.widget.grid_view)
        self.assertIsNotNone(self.widget.search_box)
        self.assertIsNotNone(self.widget.category_filter)
        self.assertIsNotNone(self.widget.format_filter)
        self.assertIsNotNone(self.widget.file_tree)
        
        # Check initial view mode
        self.assertEqual(self.widget.view_mode, ViewMode.LIST)
        
        # Check that database is connected
        self.assertIsNotNone(self.widget.db_manager)
    
    def test_view_mode_switching(self) -> None:
        """Test switching between list and grid view modes."""
        # Test switching to grid view
        self.widget._set_view_mode(ViewMode.GRID)
        self.assertEqual(self.widget.view_mode, ViewMode.GRID)
        self.assertTrue(self.widget.grid_view_button.isChecked())
        self.assertFalse(self.widget.list_view_button.isChecked())
        
        # Test switching to list view
        self.widget._set_view_mode(ViewMode.LIST)
        self.assertEqual(self.widget.view_mode, ViewMode.LIST)
        self.assertTrue(self.widget.list_view_button.isChecked())
        self.assertFalse(self.widget.grid_view_button.isChecked())
    
    def test_model_loading(self) -> None:
        """Test loading models into the library."""
        # Load test model
        self.widget._load_models([self.test_stl_path])
        
        # Wait for loading to complete
        timeout = 10000  # 10 seconds
        start_time = time.time()
        
        while self.widget.loading_in_progress and (time.time() - start_time) * 1000 < timeout:
            QTest.qWait(100)
            QCoreApplication.processEvents()
        
        # Check that model was loaded
        self.assertGreater(len(self.widget.current_models), 0)
        
        # Check that model was added to database
        models = self.db_manager.get_all_models()
        self.assertGreater(len(models), 0)
    
    def test_search_filtering(self) -> None:
        """Test search functionality."""
        # Load a test model first
        self.widget._load_models([self.test_stl_path])
        
        # Wait for loading to complete
        timeout = 10000
        start_time = time.time()
        while self.widget.loading_in_progress and (time.time() - start_time) * 1000 < timeout:
            QTest.qWait(100)
            QCoreApplication.processEvents()
        
        # Test search with model name
        self.widget.search_box.setText("test_cube")
        QTest.qWait(100)
        
        # Check that proxy model filtered the results
        visible_count = self.widget.proxy_model.rowCount()
        total_count = self.widget.list_model.rowCount()
        
        if total_count > 0:
            self.assertGreater(visible_count, 0)
            self.assertLessEqual(visible_count, total_count)
        
        # Clear search
        self.widget.search_box.setText("")
        QTest.qWait(100)
        
        # Check that all models are visible again
        visible_count = self.widget.proxy_model.rowCount()
        total_count = self.widget.list_model.rowCount()
        self.assertEqual(visible_count, total_count)
    
    def test_model_selection(self) -> None:
        """Test model selection functionality."""
        # Load a test model first
        self.widget._load_models([self.test_stl_path])
        
        # Wait for loading to complete
        timeout = 10000
        start_time = time.time()
        while self.widget.loading_in_progress and (time.time() - start_time) * 1000 < timeout:
            QTest.qWait(100)
            QCoreApplication.processEvents()
        
        # Check that we have models to select
        if self.widget.proxy_model.rowCount() > 0:
            # Select the first model
            index = self.widget.proxy_model.index(0, 0)
            self.widget.list_view.setCurrentIndex(index)
            
            # Check that model ID is returned
            model_id = self.widget.get_selected_model_id()
            self.assertIsNotNone(model_id)
            self.assertIsInstance(model_id, int)
    
    def test_drag_and_drop(self) -> None:
        """Test drag and drop functionality."""
        # Create a QMimeData with file URLs
        from PySide6.QtCore import QMimeData, QUrl
        from PySide6.QtGui import QDragEnterEvent, QDropEvent
        
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(self.test_stl_path)]
        mime_data.setUrls(urls)
        
        # Test drag enter event
        drag_enter_event = QDragEnterEvent(
            self.widget.rect().center(),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )
        self.widget.dragEnterEvent(drag_enter_event)
        self.assertTrue(drag_enter_event.isAccepted())
        
        # Test drop event
        drop_event = QDropEvent(
            self.widget.rect().center(),
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier
        )
        
        # Track loading state
        initial_loading = self.widget.loading_in_progress
        
        self.widget.dropEvent(drop_event)
        
        # Check that loading was triggered
        if not initial_loading:
            # Wait a bit for loading to start
            QTest.qWait(100)
            self.assertTrue(self.widget.loading_in_progress)
    
    def test_thumbnail_generation(self) -> None:
        """Test thumbnail generation for models."""
        from gui.model_library import ThumbnailGenerator
        
        # Create thumbnail generator
        generator = ThumbnailGenerator(QSize(128, 128))
        
        # Create test model info
        model_info = {
            'filename': 'test_cube.stl',
            'format': 'stl',
            'triangle_count': 2,
            'dimensions': (1.0, 1.0, 0.0)
        }
        
        # Generate thumbnail
        thumbnail = generator.generate_thumbnail(model_info)
        
        # Check that thumbnail was created
        self.assertIsNotNone(thumbnail)
        self.assertFalse(thumbnail.isNull())
        self.assertEqual(thumbnail.size(), QSize(128, 128))
    
    def test_memory_leaks(self) -> None:
        """Test for memory leaks during repeated operations."""
        # Get initial memory usage
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Perform multiple operations
        for i in range(10):
            # Load models
            self.widget._load_models([self.test_stl_path])
            
            # Wait for loading to complete
            timeout = 10000
            start_time = time.time()
            while self.widget.loading_in_progress and (time.time() - start_time) * 1000 < timeout:
                QTest.qWait(100)
                QCoreApplication.processEvents()
            
            # Switch view modes
            self.widget._set_view_mode(ViewMode.GRID)
            QTest.qWait(50)
            self.widget._set_view_mode(ViewMode.LIST)
            QTest.qWait(50)
            
            # Clear models
            self.widget.current_models.clear()
            self.widget._update_model_view()
            
            # Force garbage collection
            gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Allow some memory increase but should be reasonable
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # Less than 50MB increase
    
    def test_ui_responsiveness(self) -> None:
        """Test that UI remains responsive during operations."""
        # Track UI responsiveness during model loading
        ui_responsive = True
        start_time = time.time()
        
        # Start loading models
        self.widget._load_models([self.test_stl_path])
        
        # Check UI responsiveness during loading
        while self.widget.loading_in_progress:
            # Try to process UI events
            QCoreApplication.processEvents()
            
            # Check if we're stuck (no progress for too long)
            elapsed = time.time() - start_time
            if elapsed > 15:  # 15 second timeout
                ui_responsive = False
                break
            
            QTest.qWait(10)
        
        # UI should remain responsive
        self.assertTrue(ui_responsive, "UI became unresponsive during model loading")


class TestModelLoadWorker(unittest.TestCase):
    """Test cases for the ModelLoadWorker class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Create QApplication if it doesn't exist
        if not QCoreApplication.instance():
            cls.app = QApplication([])
        
        # Create temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test STL files
        cls.test_files = []
        for i in range(3):
            file_path = os.path.join(cls.temp_dir, f"test_cube_{i}.stl")
            TestModelLibraryWidget._create_test_stl_file(file_path)
            cls.test_files.append(file_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_worker_thread(self) -> None:
        """Test that the worker thread loads models correctly."""
        # Track loaded models
        loaded_models = []
        
        def on_model_loaded(model_info):
            loaded_models.append(model_info)
        
        def on_finished():
            self.worker_finished = True
        
        # Create worker
        worker = ModelLoadWorker(self.test_files)
        worker.model_loaded.connect(on_model_loaded)
        worker.finished.connect(on_finished)
        
        # Track completion
        self.worker_finished = False
        
        # Start worker
        worker.start()
        
        # Wait for completion
        timeout = 15000  # 15 seconds
        start_time = time.time()
        while not self.worker_finished and (time.time() - start_time) * 1000 < timeout:
            QTest.qWait(100)
            QCoreApplication.processEvents()
        
        # Check that models were loaded
        self.assertEqual(len(loaded_models), len(self.test_files))
        self.assertTrue(self.worker_finished)
        
        # Clean up worker
        worker.quit()
        worker.wait(3000)


if __name__ == '__main__':
    unittest.main()