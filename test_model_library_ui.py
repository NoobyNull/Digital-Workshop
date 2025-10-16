#!/usr/bin/env python3
"""
Test script to verify that the model library UI is loading correctly.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from gui.model_library import ModelLibraryWidget
from core.logging_config import get_logger

def test_model_library_ui():
    """Test the model library UI loading."""
    logger = get_logger(__name__)
    logger.info("Starting model library UI test")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    try:
        # Create model library widget
        model_library = ModelLibraryWidget()
        
        # Check if UI elements are loaded
        ui_elements = {
            "search_box": model_library.search_box,
            "category_filter": model_library.category_filter,
            "format_filter": model_library.format_filter,
            "path_display": model_library.path_display,
            "file_tree": model_library.file_tree,
            "import_selected_button": model_library.import_selected_button,
            "import_folder_button": model_library.import_folder_button,
            "internal_tabs": model_library.internal_tabs,
            "view_tabs": model_library.view_tabs,
            "list_view": model_library.list_view,
            "grid_view": model_library.grid_view,
            "status_label": model_library.status_label,
            "model_count_label": model_library.model_count_label,
            "progress_bar": model_library.progress_bar,
        }
        
        # Check each UI element
        missing_elements = []
        for name, element in ui_elements.items():
            if element is None:
                missing_elements.append(name)
                logger.error(f"Missing UI element: {name}")
            else:
                logger.info(f"UI element loaded successfully: {name}")
        
        if missing_elements:
            logger.error(f"Test failed: Missing UI elements: {', '.join(missing_elements)}")
            return False
        else:
            logger.info("Test passed: All UI elements loaded successfully")
            return True
            
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        return False
    
    finally:
        # Quit application
        app.quit()

if __name__ == "__main__":
    success = test_model_library_ui()
    sys.exit(0 if success else 1)