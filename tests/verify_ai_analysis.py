"""
Verification script for AI Analysis button implementation.
"""

import sys
from pathlib import Path


def verify_button_in_code():
    """Verify that the Run AI Analysis button is in the code."""
    try:
        metadata_file = Path("src/gui/metadata_components/metadata_editor_main.py")
        content = metadata_file.read_text()
        
        # Check for button creation
        if 'self.run_ai_analysis_button = QPushButton("Run AI Analysis")' in content:
            print("[PASS] Run AI Analysis button creation found")
        else:
            print("[FAIL] Run AI Analysis button creation not found")
            return False
        
        # Check for button connection
        if 'self.run_ai_analysis_button.clicked.connect(self._run_ai_analysis)' in content:
            print("[PASS] Run AI Analysis button connection found")
        else:
            print("[FAIL] Run AI Analysis button connection not found")
            return False
        
        # Check for tooltip
        if 'self.run_ai_analysis_button.setToolTip' in content:
            print("[PASS] Run AI Analysis button tooltip found")
        else:
            print("[FAIL] Run AI Analysis button tooltip not found")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Button verification failed: {e}")
        return False


def verify_ai_analysis_method():
    """Verify that the _run_ai_analysis method exists."""
    try:
        metadata_file = Path("src/gui/metadata_components/metadata_editor_main.py")
        content = metadata_file.read_text()
        
        # Check for method definition
        if 'def _run_ai_analysis(self) -> None:' in content:
            print("[PASS] _run_ai_analysis method definition found")
        else:
            print("[FAIL] _run_ai_analysis method definition not found")
            return False
        
        # Check for key functionality
        if 'self.run_ai_analysis_button.setEnabled(False)' in content:
            print("[PASS] Button disable logic found")
        else:
            print("[FAIL] Button disable logic not found")
            return False
        
        if 'ai_service.analyze_image(thumbnail_path)' in content:
            print("[PASS] AI service call found")
        else:
            print("[FAIL] AI service call not found")
            return False
        
        if 'self._apply_ai_results(result)' in content:
            print("[PASS] Apply results call found")
        else:
            print("[FAIL] Apply results call not found")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Method verification failed: {e}")
        return False


def verify_apply_ai_results_method():
    """Verify that the _apply_ai_results method exists."""
    try:
        metadata_file = Path("src/gui/metadata_components/metadata_editor_main.py")
        content = metadata_file.read_text()
        
        # Check for method definition
        if 'def _apply_ai_results(self, result: Dict[str, Any]) -> None:' in content:
            print("[PASS] _apply_ai_results method definition found")
        else:
            print("[FAIL] _apply_ai_results method definition not found")
            return False
        
        # Check for field updates
        if 'self.title_edit.setText(result[\'title\'])' in content:
            print("[PASS] Title field update found")
        else:
            print("[FAIL] Title field update not found")
            return False
        
        if 'self.description_edit.setPlainText(result[\'description\'])' in content:
            print("[PASS] Description field update found")
        else:
            print("[FAIL] Description field update not found")
            return False
        
        if 'self.keywords_edit.setText(keywords_str)' in content:
            print("[PASS] Keywords field update found")
        else:
            print("[FAIL] Keywords field update not found")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Apply results verification failed: {e}")
        return False


def verify_get_ai_service_method():
    """Verify that the _get_ai_service method exists."""
    try:
        metadata_file = Path("src/gui/metadata_components/metadata_editor_main.py")
        content = metadata_file.read_text()
        
        # Check for method definition
        if 'def _get_ai_service(self):' in content:
            print("[PASS] _get_ai_service method definition found")
        else:
            print("[FAIL] _get_ai_service method definition not found")
            return False
        
        # Check for parent traversal
        if 'parent = self.parent()' in content:
            print("[PASS] Parent traversal logic found")
        else:
            print("[FAIL] Parent traversal logic not found")
            return False
        
        # Check for AI service import
        if 'from src.gui.services.ai_description_service import AIDescriptionService' in content:
            print("[PASS] AI service import found")
        else:
            print("[FAIL] AI service import not found")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Get AI service verification failed: {e}")
        return False


def verify_ai_prompts_updated():
    """Verify that AI prompts have been updated for JSON format."""
    try:
        ai_service_file = Path("src/gui/services/ai_description_service.py")
        content = ai_service_file.read_text()
        
        # Check for JSON format in prompts
        if 'Return ONLY valid JSON' in content:
            print("[PASS] JSON format requirement found in prompts")
        else:
            print("[FAIL] JSON format requirement not found in prompts")
            return False
        
        # Check for metadata_keywords field
        if 'metadata_keywords' in content:
            print("[PASS] metadata_keywords field found in prompts")
        else:
            print("[FAIL] metadata_keywords field not found in prompts")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] AI prompts verification failed: {e}")
        return False


def main():
    """Run all verifications."""
    print("="*60)
    print("AI Analysis Button Implementation Verification")
    print("="*60)
    print()
    
    results = []
    
    print("1. Verifying button in code...")
    results.append(verify_button_in_code())
    print()
    
    print("2. Verifying _run_ai_analysis method...")
    results.append(verify_ai_analysis_method())
    print()
    
    print("3. Verifying _apply_ai_results method...")
    results.append(verify_apply_ai_results_method())
    print()
    
    print("4. Verifying _get_ai_service method...")
    results.append(verify_get_ai_service_method())
    print()
    
    print("5. Verifying AI prompts updated...")
    results.append(verify_ai_prompts_updated())
    print()
    
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Verification Results: {passed}/{total} passed")
    print("="*60)
    
    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

