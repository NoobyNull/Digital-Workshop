"""
Test suite for the metadata editor widget.

This module provides comprehensive testing for the metadata editor functionality,
including form validation, database integration, and UI interactions.
"""

import gc
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtTest import QTest

from core.database_manager import DatabaseManager
from core.logging_config import get_logger
from gui.metadata_editor import MetadataEditorWidget, StarRatingWidget


class TestStarRatingWidget(unittest.TestCase):
    """Test cases for the StarRatingWidget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up each test."""
        self.widget = StarRatingWidget()
    
    def tearDown(self):
        """Clean up after each test."""
        self.widget.deleteLater()
        gc.collect()
    
    def test_initial_state(self):
        """Test the initial state of the widget."""
        self.assertEqual(self.widget.get_rating(), 0)
        self.assertEqual(self.widget.hover_rating, 0)
        self.assertEqual(self.widget.star_count, 5)
        self.assertEqual(self.widget.star_size, 24)
    
    def test_set_rating(self):
        """Test setting the rating."""
        # Test valid ratings
        for rating in range(1, 6):
            self.widget.set_rating(rating)
            self.assertEqual(self.widget.get_rating(), rating)
        
        # Test invalid ratings
        self.widget.set_rating(0)
        self.assertEqual(self.widget.get_rating(), 0)
        
        # Test out of range ratings
        original_rating = self.widget.get_rating()
        self.widget.set_rating(10)  # Should be ignored
        self.assertEqual(self.widget.get_rating(), original_rating)
        
        self.widget.set_rating(-1)  # Should be ignored
        self.assertEqual(self.widget.get_rating(), original_rating)
    
    def test_reset_rating(self):
        """Test resetting the rating."""
        self.widget.set_rating(3)
        self.assertEqual(self.widget.get_rating(), 3)
        
        self.widget.reset_rating()
        self.assertEqual(self.widget.get_rating(), 0)
    
    def test_rating_signal(self):
        """Test that the rating_changed signal is emitted."""
        signal_received = []
        
        def on_rating_changed(rating):
            signal_received.append(rating)
        
        self.widget.rating_changed.connect(on_rating_changed)
        
        # Test signal emission
        self.widget.set_rating(3)
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], 3)
        
        # Test signal on reset
        self.widget.reset_rating()
        self.assertEqual(len(signal_received), 2)
        self.assertEqual(signal_received[1], 0)
    
    def test_mouse_interaction(self):
        """Test mouse interaction with the widget."""
        # Test clicking on different stars
        for i in range(1, 6):
            # Calculate position for star i
            x = (i - 1) * (self.widget.star_size + self.widget.star_spacing) + self.widget.star_size // 2
            y = self.widget.star_size // 2
            
            # Click on the star
            QTest.mouseClick(self.widget, Qt.LeftButton, pos=(x, y))
            self.assertEqual(self.widget.get_rating(), i)
    
    def test_hover_effect(self):
        """Test hover effects."""
        # Test hovering over stars
        for i in range(1, 6):
            x = (i - 1) * (self.widget.star_size + self.widget.star_spacing) + self.widget.star_size // 2
            y = self.widget.star_size // 2
            
            QTest.mouseMove(self.widget, pos=(x, y))
            self.assertEqual(self.widget.hover_rating, i)
        
        # Test leaving the widget
        QTest.mouseMove(self.widget, pos=(-10, -10))
        QTest.qWait(100)  # Allow time for leave event
        self.assertEqual(self.widget.hover_rating, 0)


class TestMetadataEditorWidget(unittest.TestCase):
    """Test cases for the MetadataEditorWidget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
        
        # Create a temporary database for testing
        cls.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db.close()
        cls.db_path = cls.temp_db.name
        
        # Initialize database
        cls.db_manager = DatabaseManager(cls.db_path)
        
        # Add a test model
        cls.test_model_id = cls.db_manager.add_model(
            filename="test_model.stl",
            format="stl",
            file_path="/path/to/test_model.stl",
            file_size=1024
        )
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test class."""
        # Close database connection
        cls.db_manager.close()
        
        # Remove temporary database
        try:
            os.unlink(cls.db_path)
        except:
            pass
    
    def setUp(self):
        """Set up each test."""
        self.widget = MetadataEditorWidget()
        
        # Mock the database manager to use our test database
        self.widget.db_manager = self.db_manager
    
    def tearDown(self):
        """Clean up after each test."""
        self.widget.cleanup()
        self.widget.deleteLater()
        gc.collect()
    
    def test_initial_state(self):
        """Test the initial state of the widget."""
        self.assertIsNone(self.widget.current_model_id)
        self.assertEqual(self.widget.original_metadata, {})
        self.assertFalse(self.widget.has_unsaved_changes())
    
    def test_load_model_metadata(self):
        """Test loading model metadata."""
        # Add metadata for the test model
        self.db_manager.add_model_metadata(
            model_id=self.test_model_id,
            title="Test Model",
            description="A test model for testing",
            keywords="test, model, stl",
            category="Test Category",
            source="Test Source",
            rating=4
        )
        
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Check that metadata was loaded
        self.assertEqual(self.widget.current_model_id, self.test_model_id)
        self.assertEqual(self.widget.title_field.text(), "Test Model")
        self.assertEqual(self.widget.description_field.toPlainText(), "A test model for testing")
        self.assertEqual(self.widget.keywords_field.text(), "test, model, stl")
        self.assertEqual(self.widget.category_field.currentText(), "Test Category")
        self.assertEqual(self.widget.source_field.text(), "Test Source")
        self.assertEqual(self.widget.star_rating.get_rating(), 4)
        
        # Check original metadata
        self.assertEqual(self.widget.original_metadata['title'], "Test Model")
        self.assertEqual(self.widget.original_metadata['description'], "A test model for testing")
        self.assertEqual(self.widget.original_metadata['keywords'], "test, model, stl")
        self.assertEqual(self.widget.original_metadata['category'], "Test Category")
        self.assertEqual(self.widget.original_metadata['source'], "Test Source")
        self.assertEqual(self.widget.original_metadata['rating'], 4)
    
    def test_load_nonexistent_model(self):
        """Test loading metadata for a non-existent model."""
        # Try to load metadata for a non-existent model
        self.widget.load_model_metadata(9999)
        
        # Widget should be cleared
        self.assertIsNone(self.widget.current_model_id)
        self.assertEqual(self.widget.title_field.text(), "")
        self.assertEqual(self.widget.description_field.toPlainText(), "")
        self.assertEqual(self.widget.keywords_field.text(), "")
        self.assertEqual(self.widget.category_field.currentText(), "")
        self.assertEqual(self.widget.source_field.text(), "")
        self.assertEqual(self.widget.star_rating.get_rating(), 0)
    
    def test_unsaved_changes_detection(self):
        """Test detection of unsaved changes."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Initially no unsaved changes
        self.assertFalse(self.widget.has_unsaved_changes())
        
        # Change title
        self.widget.title_field.setText("New Title")
        self.assertTrue(self.widget.has_unsaved_changes())
        
        # Reset form
        self.widget._reset_form()
        self.assertFalse(self.widget.has_unsaved_changes())
        
        # Change rating
        self.widget.star_rating.set_rating(3)
        self.assertTrue(self.widget.has_unsaved_changes())
        
        # Reset form again
        self.widget._reset_form()
        self.assertFalse(self.widget.has_unsaved_changes())
    
    def test_save_metadata(self):
        """Test saving metadata."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Change metadata
        self.widget.title_field.setText("Updated Model")
        self.widget.description_field.setPlainText("Updated description")
        self.widget.keywords_field.setText("updated, model")
        self.widget.category_field.setCurrentText("Updated Category")
        self.widget.source_field.setText("Updated Source")
        self.widget.star_rating.set_rating(5)
        
        # Save metadata
        with patch.object(QMessageBox, 'information'):
            self.widget._save_metadata()
        
        # Check that metadata was saved
        model = self.db_manager.get_model(self.test_model_id)
        self.assertEqual(model['title'], "Updated Model")
        self.assertEqual(model['description'], "Updated description")
        self.assertEqual(model['keywords'], "updated, model")
        self.assertEqual(model['category'], "Updated Category")
        self.assertEqual(model['source'], "Updated Source")
        self.assertEqual(model['rating'], 5)
        
        # Check that original metadata was updated
        self.assertEqual(self.widget.original_metadata['title'], "Updated Model")
        self.assertEqual(self.widget.original_metadata['description'], "Updated description")
        self.assertEqual(self.widget.original_metadata['keywords'], "updated, model")
        self.assertEqual(self.widget.original_metadata['category'], "Updated Category")
        self.assertEqual(self.widget.original_metadata['source'], "Updated Source")
        self.assertEqual(self.widget.original_metadata['rating'], 5)
    
    def test_save_new_metadata(self):
        """Test saving metadata for a model without existing metadata."""
        # Load model without metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Add metadata
        self.widget.title_field.setText("New Model")
        self.widget.description_field.setPlainText("New description")
        self.widget.keywords_field.setText("new, model")
        self.widget.category_field.setCurrentText("New Category")
        self.widget.source_field.setText("New Source")
        self.widget.star_rating.set_rating(3)
        
        # Save metadata
        with patch.object(QMessageBox, 'information'):
            self.widget._save_metadata()
        
        # Check that metadata was saved
        model = self.db_manager.get_model(self.test_model_id)
        self.assertEqual(model['title'], "New Model")
        self.assertEqual(model['description'], "New description")
        self.assertEqual(model['keywords'], "new, model")
        self.assertEqual(model['category'], "New Category")
        self.assertEqual(model['source'], "New Source")
        self.assertEqual(model['rating'], 3)
    
    def test_cancel_changes(self):
        """Test canceling changes."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Get original title
        original_title = self.widget.title_field.text()
        
        # Change title
        self.widget.title_field.setText("Changed Title")
        self.assertEqual(self.widget.title_field.text(), "Changed Title")
        
        # Cancel changes
        self.widget._cancel_changes()
        
        # Check that title was restored
        self.assertEqual(self.widget.title_field.text(), original_title)
    
    def test_reset_form(self):
        """Test resetting the form."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Change fields
        self.widget.title_field.setText("Changed Title")
        self.widget.description_field.setPlainText("Changed description")
        self.widget.star_rating.set_rating(2)
        
        # Reset form
        self.widget._reset_form()
        
        # Check that fields were restored to original values
        self.assertEqual(self.widget.title_field.text(), self.widget.original_metadata.get('title', ''))
        self.assertEqual(self.widget.description_field.toPlainText(), self.widget.original_metadata.get('description', ''))
        self.assertEqual(self.widget.star_rating.get_rating(), self.widget.original_metadata.get('rating', 0))
    
    def test_clear_form(self):
        """Test clearing the form."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Clear form
        self.widget._clear_form()
        
        # Check that form was cleared
        self.assertIsNone(self.widget.current_model_id)
        self.assertEqual(self.widget.title_field.text(), "")
        self.assertEqual(self.widget.description_field.toPlainText(), "")
        self.assertEqual(self.widget.keywords_field.text(), "")
        self.assertEqual(self.widget.category_field.currentText(), "")
        self.assertEqual(self.widget.source_field.text(), "")
        self.assertEqual(self.widget.star_rating.get_rating(), 0)
        self.assertEqual(self.widget.original_metadata, {})
    
    def test_validation(self):
        """Test input validation."""
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Test valid input
        self.widget.title_field.setText("Valid Title")
        self.widget.keywords_field.setText("valid, keywords")
        self.widget.star_rating.set_rating(3)
        self.assertTrue(self.widget._validate_input())
        
        # Test too many keywords
        too_many_keywords = ",".join([f"keyword{i}" for i in range(25)])
        self.widget.keywords_field.setText(too_many_keywords)
        with patch.object(QMessageBox, 'warning') as mock_warning:
            result = self.widget._validate_input()
            self.assertFalse(result)
            mock_warning.assert_called_once()
        
        # Reset keywords
        self.widget.keywords_field.setText("valid, keywords")
        
        # Test invalid rating
        self.widget.star_rating.set_rating(10)  # Invalid rating
        with patch.object(QMessageBox, 'warning') as mock_warning:
            result = self.widget._validate_input()
            self.assertFalse(result)
            mock_warning.assert_called_once()
    
    def test_signal_emission(self):
        """Test signal emission."""
        # Track signals
        metadata_saved_signals = []
        metadata_changed_signals = []
        
        def on_metadata_saved(model_id):
            metadata_saved_signals.append(model_id)
        
        def on_metadata_changed(model_id):
            metadata_changed_signals.append(model_id)
        
        self.widget.metadata_saved.connect(on_metadata_saved)
        self.widget.metadata_changed.connect(on_metadata_changed)
        
        # Load metadata
        self.widget.load_model_metadata(self.test_model_id)
        
        # Change field - should emit metadata_changed
        self.widget.title_field.setText("Changed")
        self.assertEqual(len(metadata_changed_signals), 1)
        self.assertEqual(metadata_changed_signals[0], self.test_model_id)
        
        # Save metadata - should emit metadata_saved
        with patch.object(QMessageBox, 'information'):
            self.widget._save_metadata()
        self.assertEqual(len(metadata_saved_signals), 1)
        self.assertEqual(metadata_saved_signals[0], self.test_model_id)
    
    def test_category_loading(self):
        """Test loading categories from the database."""
        # Add test categories
        self.db_manager.add_category("Test Category 1", "#FF0000", 1)
        self.db_manager.add_category("Test Category 2", "#00FF00", 2)
        
        # Reload categories
        self.widget._load_categories()
        
        # Check that categories were loaded
        self.assertGreater(self.widget.category_field.count(), 2)  # At least empty + 2 categories
        self.assertTrue(self.widget.category_field.findText("Test Category 1") >= 0)
        self.assertTrue(self.widget.category_field.findText("Test Category 2") >= 0)
    
    def test_model_info_display(self):
        """Test the model information display."""
        # Create a model with known properties
        model_info = {
            'id': self.test_model_id,
            'filename': 'test_model.stl',
            'format': 'stl',
            'file_size': 2048,  # 2KB
            'triangle_count': 1000
        }
        
        # Update model info
        self.widget._update_model_info(model_info)
        
        # Check that info was displayed correctly
        self.assertEqual(self.widget.model_filename_label.text(), 'test_model.stl')
        self.assertEqual(self.widget.model_format_label.text(), 'STL')
        self.assertEqual(self.widget.model_size_label.text(), '2.0 KB')
        self.assertEqual(self.widget.model_triangles_label.text(), '1,000')


class TestMetadataEditorIntegration(unittest.TestCase):
    """Integration tests for the metadata editor with the database."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
        
        # Create a temporary database for testing
        cls.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.temp_db.close()
        cls.db_path = cls.temp_db.name
        
        # Initialize database
        cls.db_manager = DatabaseManager(cls.db_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test class."""
        # Close database connection
        cls.db_manager.close()
        
        # Remove temporary database
        try:
            os.unlink(cls.db_path)
        except:
            pass
    
    def test_metadata_workflow(self):
        """Test a complete metadata workflow."""
        # Create a widget
        widget = MetadataEditorWidget()
        widget.db_manager = self.db_manager
        
        try:
            # Add a test model
            model_id = self.db_manager.add_model(
                filename="workflow_test.stl",
                format="stl",
                file_path="/path/to/workflow_test.stl",
                file_size=1024
            )
            
            # Load metadata (should be empty)
            widget.load_model_metadata(model_id)
            self.assertEqual(widget.title_field.text(), "")
            
            # Add metadata
            widget.title_field.setText("Workflow Test Model")
            widget.description_field.setPlainText("A model for testing the workflow")
            widget.keywords_field.setText("workflow, test, model")
            widget.category_field.setCurrentText("Test Category")
            widget.source_field.setText("Test Source")
            widget.star_rating.set_rating(4)
            
            # Save metadata
            with patch.object(QMessageBox, 'information'):
                widget._save_metadata()
            
            # Verify metadata was saved
            model = self.db_manager.get_model(model_id)
            self.assertEqual(model['title'], "Workflow Test Model")
            self.assertEqual(model['description'], "A model for testing the workflow")
            self.assertEqual(model['keywords'], "workflow, test, model")
            self.assertEqual(model['category'], "Test Category")
            self.assertEqual(model['source'], "Test Source")
            self.assertEqual(model['rating'], 4)
            
            # Clear and reload metadata
            widget._clear_form()
            widget.load_model_metadata(model_id)
            
            # Verify metadata was loaded correctly
            self.assertEqual(widget.title_field.text(), "Workflow Test Model")
            self.assertEqual(widget.description_field.toPlainText(), "A model for testing the workflow")
            self.assertEqual(widget.keywords_field.text(), "workflow, test, model")
            self.assertEqual(widget.category_field.currentText(), "Test Category")
            self.assertEqual(widget.source_field.text(), "Test Source")
            self.assertEqual(widget.star_rating.get_rating(), 4)
            
            # Update metadata
            widget.title_field.setText("Updated Workflow Test Model")
            widget.star_rating.set_rating(5)
            
            # Save updated metadata
            with patch.object(QMessageBox, 'information'):
                widget._save_metadata()
            
            # Verify metadata was updated
            model = self.db_manager.get_model(model_id)
            self.assertEqual(model['title'], "Updated Workflow Test Model")
            self.assertEqual(model['rating'], 5)
            
        finally:
            # Clean up
            widget.cleanup()
            widget.deleteLater()
            gc.collect()


if __name__ == '__main__':
    unittest.main()