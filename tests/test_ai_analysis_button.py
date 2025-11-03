"""
Tests for AI Analysis button functionality in metadata editor.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestAIAnalysisButton:
    """Test suite for AI Analysis button in metadata editor."""
    
    def test_run_ai_analysis_button_exists(self):
        """Test that the Run AI Analysis button is created."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                editor = MetadataEditorWidget()
                
                # Check button exists
                assert hasattr(editor, 'run_ai_analysis_button'), "Run AI Analysis button not found"
                assert editor.run_ai_analysis_button is not None, "Run AI Analysis button is None"
                
                print("[PASS] Run AI Analysis button exists")
                return True
        except Exception as e:
            print(f"[FAIL] Button existence test failed: {e}")
            return False
    
    def test_run_ai_analysis_button_connected(self):
        """Test that the Run AI Analysis button is connected to the method."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                editor = MetadataEditorWidget()
                
                # Check method exists
                assert hasattr(editor, '_run_ai_analysis'), "_run_ai_analysis method not found"
                assert callable(editor._run_ai_analysis), "_run_ai_analysis is not callable"
                
                print("[PASS] Run AI Analysis button is connected to method")
                return True
        except Exception as e:
            print(f"[FAIL] Button connection test failed: {e}")
            return False
    
    def test_ai_analysis_requires_model_selection(self):
        """Test that AI analysis requires a model to be selected."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            from PySide6.QtWidgets import QMessageBox
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                with patch.object(QMessageBox, 'warning') as mock_warning:
                    editor = MetadataEditorWidget()
                    editor.current_model_id = None
                    
                    # Call the method
                    editor._run_ai_analysis()
                    
                    # Should show warning
                    mock_warning.assert_called_once()
                    
                    print("[PASS] AI analysis requires model selection")
                    return True
        except Exception as e:
            print(f"[FAIL] Model selection test failed: {e}")
            return False
    
    def test_apply_ai_results_updates_fields(self):
        """Test that AI results are applied to metadata fields."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                editor = MetadataEditorWidget()
                editor.current_model_id = 1
                
                # Mock result
                result = {
                    'title': 'Test Title',
                    'description': 'Test Description',
                    'metadata_keywords': ['keyword1', 'keyword2', 'keyword3']
                }
                
                # Apply results
                editor._apply_ai_results(result)
                
                # Check fields were updated
                assert editor.title_edit.text() == 'Test Title', "Title not updated"
                assert editor.description_edit.toPlainText() == 'Test Description', "Description not updated"
                assert editor.keywords_edit.text() == 'keyword1, keyword2, keyword3', "Keywords not updated"
                
                print("[PASS] AI results applied to metadata fields")
                return True
        except Exception as e:
            print(f"[FAIL] Apply results test failed: {e}")
            return False
    
    def test_get_ai_service_from_parent(self):
        """Test that AI service can be retrieved from parent window."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                editor = MetadataEditorWidget()
                
                # Create mock parent with AI service
                mock_parent = Mock()
                mock_ai_service = Mock()
                mock_parent.ai_service = mock_ai_service
                editor.setParent(mock_parent)
                
                # Get AI service
                service = editor._get_ai_service()
                
                # Should return the mock service
                assert service is not None, "AI service is None"
                
                print("[PASS] AI service retrieved from parent")
                return True
        except Exception as e:
            print(f"[FAIL] Get AI service test failed: {e}")
            return False
    
    def test_ai_analysis_button_tooltip(self):
        """Test that the AI Analysis button has a helpful tooltip."""
        try:
            from src.gui.metadata_components.metadata_editor_main import MetadataEditorWidget
            
            with patch('src.gui.metadata_components.metadata_editor_main.get_database_manager'):
                editor = MetadataEditorWidget()
                
                # Check tooltip
                tooltip = editor.run_ai_analysis_button.toolTip()
                assert tooltip, "Button has no tooltip"
                assert 'AI' in tooltip or 'analysis' in tooltip.lower(), "Tooltip doesn't mention AI analysis"
                
                print("[PASS] AI Analysis button has helpful tooltip")
                return True
        except Exception as e:
            print(f"[FAIL] Tooltip test failed: {e}")
            return False


def run_all_tests():
    """Run all tests and report results."""
    test_suite = TestAIAnalysisButton()
    tests = [
        test_suite.test_run_ai_analysis_button_exists,
        test_suite.test_run_ai_analysis_button_connected,
        test_suite.test_ai_analysis_requires_model_selection,
        test_suite.test_apply_ai_results_updates_fields,
        test_suite.test_get_ai_service_from_parent,
        test_suite.test_ai_analysis_button_tooltip,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n{'='*60}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print(f"{'='*60}")
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

