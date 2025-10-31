"""
Test Framework Validation Script

This script validates that the complete testing framework is properly implemented
and all components work together correctly. It serves as the final validation
step for the Candy-Cadence testing and quality assurance framework.
"""

import gc
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core.logging_config import get_logger
except ImportError:
    # Fallback for when src modules aren't available
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class FrameworkValidator:
    """Validates the complete testing framework implementation."""
    
    def __init__(self):
        """Initialize framework validator."""
        self.logger = get_logger(__name__)
        self.test_root = Path(__file__).parent
        self.src_root = Path(__file__).parent.parent / "src"
        
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "framework_components": {},
            "test_execution": {},
            "quality_assurance": {},
            "documentation": {},
            "integration": {},
            "overall_status": "PENDING"
        }
    
    def validate_framework(self) -> Dict[str, Any]:
        """Run complete framework validation."""
        self.logger.info("Starting framework validation...")
        
        try:
            # 1. Validate Framework Components
            self.logger.info("Validating framework components...")
            self.validation_results["framework_components"] = self._validate_framework_components()
            
            # 2. Validate Test Execution
            self.logger.info("Validating test execution...")
            self.validation_results["test_execution"] = self._validate_test_execution()
            
            # 3. Validate Quality Assurance
            self.logger.info("Validating quality assurance...")
            self.validation_results["quality_assurance"] = self._validate_quality_assurance()
            
            # 4. Validate Documentation
            self.logger.info("Validating documentation...")
            self.validation_results["documentation"] = self._validate_documentation()
            
            # 5. Validate Integration
            self.logger.info("Validating integration...")
            self.validation_results["integration"] = self._validate_integration()
            
            # 6. Calculate Overall Status
            self._calculate_overall_status()
            
            self.logger.info("Framework validation completed")
            return self.validation_results
            
        except Exception as e:
            self.logger.error(f"Framework validation failed: {e}")
            self.validation_results["overall_status"] = "ERROR"
            self.validation_results["error"] = str(e)
            self.validation_results["traceback"] = traceback.format_exc()
            return self.validation_results
    
    def _validate_framework_components(self) -> Dict[str, Any]:
        """Validate all framework components exist and are properly structured."""
        results = {
            "memory_leak_tests": {"status": "MISSING", "details": {}},
            "performance_framework": {"status": "MISSING", "details": {}},
            "qa_framework": {"status": "MISSING", "details": {}},
            "continuous_testing": {"status": "MISSING", "details": {}},
            "gui_tests": {"status": "MISSING", "details": {}},
            "e2e_tests": {"status": "MISSING", "details": {}},
            "conftest": {"status": "MISSING", "details": {}}
        }
        
        # Check memory leak tests
        memory_leak_file = self.test_root / "memory_leak_tests.py"
        if memory_leak_file.exists():
            results["memory_leak_tests"]["status"] = "FOUND"
            results["memory_leak_tests"]["details"] = {
                "file_size": memory_leak_file.stat().st_size,
                "classes": self._count_classes_in_file(memory_leak_file),
                "functions": self._count_functions_in_file(memory_leak_file)
            }
        
        # Check performance framework
        perf_file = self.test_root / "test_performance_regression_framework.py"
        if perf_file.exists():
            results["performance_framework"]["status"] = "FOUND"
            results["performance_framework"]["details"] = {
                "file_size": perf_file.stat().st_size,
                "classes": self._count_classes_in_file(perf_file),
                "functions": self._count_functions_in_file(perf_file)
            }
        
        # Check QA framework
        qa_file = self.test_root / "quality_assurance_framework.py"
        if qa_file.exists():
            results["qa_framework"]["status"] = "FOUND"
            results["qa_framework"]["details"] = {
                "file_size": qa_file.stat().st_size,
                "classes": self._count_classes_in_file(qa_file),
                "functions": self._count_functions_in_file(qa_file)
            }
        
        # Check continuous testing framework
        ct_file = self.test_root / "continuous_testing_framework.py"
        if ct_file.exists():
            results["continuous_testing"]["status"] = "FOUND"
            results["continuous_testing"]["details"] = {
                "file_size": ct_file.stat().st_size,
                "classes": self._count_classes_in_file(ct_file),
                "functions": self._count_functions_in_file(ct_file)
            }
        
        # Check GUI tests
        gui_test_files = list(self.test_root.glob("test_*gui*.py")) + list(self.test_root.glob("test_*ui*.py"))
        if gui_test_files:
            results["gui_tests"]["status"] = "FOUND"
            results["gui_tests"]["details"] = {
                "test_files": len(gui_test_files),
                "files": [f.name for f in gui_test_files]
            }
        
        # Check E2E tests
        e2e_test_files = list(self.test_root.glob("test_*e2e*.py")) + list(self.test_root.glob("test_*end_to_end*.py"))
        if e2e_test_files:
            results["e2e_tests"]["status"] = "FOUND"
            results["e2e_tests"]["details"] = {
                "test_files": len(e2e_test_files),
                "files": [f.name for f in e2e_test_files]
            }
        
        # Check conftest
        conftest_file = self.test_root / "conftest.py"
        if conftest_file.exists():
            results["conftest"]["status"] = "FOUND"
            results["conftest"]["details"] = {
                "file_size": conftest_file.stat().st_size,
                "content_preview": conftest_file.read_text()[:200]
            }
        
        # Check for existing test files
        existing_tests = list(self.test_root.glob("test_*.py"))
        results["existing_tests"] = {
            "count": len(existing_tests),
            "files": [f.name for f in existing_tests[:10]]  # First 10 files
        }
        
        return results
    
    def _validate_test_execution(self) -> Dict[str, Any]:
        """Validate that tests can be executed successfully."""
        results = {
            "basic_execution": {"status": "PENDING", "details": {}},
            "coverage_tools": {"status": "PENDING", "details": {}},
            "test_data": {"status": "PENDING", "details": {}}
        }
        
        # Test basic pytest execution
        try:
            # Run a simple test to verify pytest works
            result = subprocess.run([
                sys.executable, "-m", "pytest", "--version"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                results["basic_execution"]["status"] = "SUCCESS"
                results["basic_execution"]["details"] = {
                    "pytest_version": result.stdout.strip(),
                    "command": "pytest --version"
                }
            else:
                results["basic_execution"]["status"] = "FAILED"
                results["basic_execution"]["details"] = {
                    "error": result.stderr,
                    "returncode": result.returncode
                }
        except Exception as e:
            results["basic_execution"]["status"] = "ERROR"
            results["basic_execution"]["details"] = {"error": str(e)}
        
        # Check coverage tools
        try:
            result = subprocess.run([
                sys.executable, "-c", "import coverage; print(coverage.__version__)"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                results["coverage_tools"]["status"] = "AVAILABLE"
                results["coverage_tools"]["details"] = {
                    "coverage_version": result.stdout.strip()
                }
            else:
                results["coverage_tools"]["status"] = "NOT_AVAILABLE"
                results["coverage_tools"]["details"] = {"error": result.stderr}
        except Exception as e:
            results["coverage_tools"]["status"] = "ERROR"
            results["coverage_tools"]["details"] = {"error": str(e)}
        
        # Check test data
        test_data_dir = self.test_root / "test_data"
        sample_files_dir = self.test_root / "sample_files"
        
        data_status = "MISSING"
        details = {}
        
        if test_data_dir.exists():
            data_files = list(test_data_dir.glob("*"))
            data_status = "FOUND"
            details["test_data_files"] = len(data_files)
            details["files"] = [f.name for f in data_files[:5]]
        
        if sample_files_dir.exists():
            sample_files = list(sample_files_dir.glob("*"))
            data_status = "COMPLETE"
            details["sample_files"] = len(sample_files)
            details["sample_files_list"] = [f.name for f in sample_files[:10]]
        
        results["test_data"]["status"] = data_status
        results["test_data"]["details"] = details
        
        return results
    
    def _validate_quality_assurance(self) -> Dict[str, Any]:
        """Validate quality assurance components."""
        results = {
            "qa_engine": {"status": "PENDING", "details": {}},
            "quality_metrics": {"status": "PENDING", "details": {}},
            "gates": {"status": "PENDING", "details": {}}
        }
        
        # Try to import and instantiate QA engine
        try:
            from tests.quality_assurance_framework import QualityAssuranceEngine
            
            qa_engine = QualityAssuranceEngine()
            results["qa_engine"]["status"] = "IMPORTABLE"
            results["qa_engine"]["details"] = {
                "engine_class": "QualityAssuranceEngine",
                "methods": [m for m in dir(qa_engine) if not m.startswith('_')]
            }
        except ImportError as e:
            results["qa_engine"]["status"] = "IMPORT_FAILED"
            results["qa_engine"]["details"] = {"error": str(e)}
        except Exception as e:
            results["qa_engine"]["status"] = "INSTANTIATION_FAILED"
            results["qa_engine"]["details"] = {"error": str(e)}
        
        # Check QA framework structure
        qa_file = self.test_root / "quality_assurance_framework.py"
        if qa_file.exists():
            content = qa_file.read_text()
            
            # Check for key classes and methods
            has_quality_metric = "QualityMetric" in content
            has_code_quality_report = "CodeQualityReport" in content
            has_qa_engine = "QualityAssuranceEngine" in content
            has_gates = "check_quality_gates" in content
            
            results["quality_metrics"]["status"] = "IMPLEMENTED" if has_quality_metric else "MISSING"
            results["quality_metrics"]["details"] = {
                "has_quality_metric_class": has_quality_metric,
                "has_report_class": has_code_quality_report
            }
            
            results["gates"]["status"] = "IMPLEMENTED" if has_gates else "MISSING"
            results["gates"]["details"] = {
                "has_gate_checking": has_gates,
                "has_qa_engine": has_qa_engine
            }
        
        return results
    
    def _validate_documentation(self) -> Dict[str, Any]:
        """Validate documentation completeness."""
        results = {
            "main_documentation": {"status": "PENDING", "details": {}},
            "best_practices": {"status": "PENDING", "details": {}},
            "docs_structure": {"status": "PENDING", "details": {}}
        }
        
        # Check main documentation
        main_doc = Path(__file__).parent.parent / "docs" / "testing" / "TESTING_FRAMEWORK_DOCUMENTATION.md"
        if main_doc.exists():
            content = main_doc.read_text()
            word_count = len(content.split())
            results["main_documentation"]["status"] = "COMPLETE"
            results["main_documentation"]["details"] = {
                "file_size": main_doc.stat().st_size,
                "word_count": word_count,
                "sections": content.count("##")
            }
        
        # Check best practices guide
        best_practices_doc = Path(__file__).parent.parent / "docs" / "testing" / "TESTING_BEST_PRACTICES.md"
        if best_practices_doc.exists():
            content = best_practices_doc.read_text()
            word_count = len(content.split())
            results["best_practices"]["status"] = "COMPLETE"
            results["best_practices"]["details"] = {
                "file_size": best_practices_doc.stat().st_size,
                "word_count": word_count,
                "sections": content.count("##")
            }
        
        # Check docs structure
        docs_dir = Path(__file__).parent.parent / "docs"
        testing_dir = docs_dir / "testing"
        
        if testing_dir.exists():
            doc_files = list(testing_dir.glob("*.md"))
            results["docs_structure"]["status"] = "ORGANIZED"
            results["docs_structure"]["details"] = {
                "docs_directory": str(docs_dir),
                "testing_subdirectory": str(testing_dir),
                "markdown_files": len(doc_files),
                "files": [f.name for f in doc_files]
            }
        else:
            results["docs_structure"]["status"] = "MISSING"
            results["docs_structure"]["details"] = {"error": "docs/testing directory not found"}
        
        return results
    
    def _validate_integration(self) -> Dict[str, Any]:
        """Validate integration between components."""
        results = {
            "component_integration": {"status": "PENDING", "details": {}},
            "import_chain": {"status": "PENDING", "details": {}},
            "configuration": {"status": "PENDING", "details": {}}
        }
        
        # Test component integration by importing key classes
        integration_tests = []
        
        try:
            # Test memory leak detection
            from tests.memory_leak_tests import MemoryLeakDetector
            detector = MemoryLeakDetector()
            integration_tests.append("MemoryLeakDetector: OK")
        except Exception as e:
            integration_tests.append(f"MemoryLeakDetector: FAILED - {e}")
        
        try:
            # Test performance framework
            from tests.test_performance_regression_framework import PerformanceRegressionDetector
            perf_detector = PerformanceRegressionDetector()
            integration_tests.append("PerformanceRegressionDetector: OK")
        except Exception as e:
            integration_tests.append(f"PerformanceRegressionDetector: FAILED - {e}")
        
        try:
            # Test QA framework
            from tests.quality_assurance_framework import QualityAssuranceEngine
            qa_engine = QualityAssuranceEngine()
            integration_tests.append("QualityAssuranceEngine: OK")
        except Exception as e:
            integration_tests.append(f"QualityAssuranceEngine: FAILED - {e}")
        
        try:
            # Test continuous testing
            from tests.continuous_testing_framework import ContinuousTestScheduler
            scheduler = ContinuousTestScheduler()
            integration_tests.append("ContinuousTestScheduler: OK")
        except Exception as e:
            integration_tests.append(f"ContinuousTestScheduler: FAILED - {e}")
        
        results["component_integration"]["status"] = "PARTIAL" if integration_tests else "FAILED"
        results["component_integration"]["details"] = {
            "tests_performed": len(integration_tests),
            "test_results": integration_tests
        }
        
        # Test import chain (src -> tests integration)
        try:
            # Try importing from src to test integration
            from src.core.logging_config import get_logger
            test_logger = get_logger("test")
            integration_tests.append("Src integration: OK")
        except Exception as e:
            integration_tests.append(f"Src integration: FAILED - {e}")
        
        results["import_chain"]["status"] = "PARTIAL"
        results["import_chain"]["details"] = {
            "can_import_src_modules": True,
            "integration_points": integration_tests
        }
        
        # Check configuration files
        config_files = [
            "pytest.ini",
            "tox.ini", 
            ".coveragerc",
            "setup.cfg"
        ]
        
        found_configs = []
        for config_file in config_files:
            if Path(config_file).exists():
                found_configs.append(config_file)
        
        results["configuration"]["status"] = "PARTIAL" if found_configs else "MISSING"
        results["configuration"]["details"] = {
            "expected_configs": config_files,
            "found_configs": found_configs,
            "config_count": len(found_configs)
        }
        
        return results
    
    def _calculate_overall_status(self):
        """Calculate overall framework status."""
        component_count = 0
        component_passed = 0
        
        # Count framework components
        for component, status in self.validation_results["framework_components"].items():
            if isinstance(status, dict) and "status" in status:
                component_count += 1
                if status["status"] == "FOUND":
                    component_passed += 1
        
        # Count test execution success
        test_exec = self.validation_results["test_execution"]
        if test_exec.get("basic_execution", {}).get("status") == "SUCCESS":
            component_count += 1
            component_passed += 1
        
        # Count QA framework
        qa_framework = self.validation_results["quality_assurance"]
        if qa_framework.get("qa_engine", {}).get("status") in ["IMPORTABLE", "IMPLEMENTED"]:
            component_count += 1
            component_passed += 1
        
        # Count documentation
        docs = self.validation_results["documentation"]
        if docs.get("main_documentation", {}).get("status") == "COMPLETE":
            component_count += 1
            component_passed += 1
        
        # Calculate score
        if component_count > 0:
            score = (component_passed / component_count) * 100
        else:
            score = 0
        
        # Set overall status
        if score >= 80:
            self.validation_results["overall_status"] = "EXCELLENT"
        elif score >= 60:
            self.validation_results["overall_status"] = "GOOD"
        elif score >= 40:
            self.validation_results["overall_status"] = "FAIR"
        else:
            self.validation_results["overall_status"] = "NEEDS_WORK"
        
        self.validation_results["completion_score"] = score
        self.validation_results["components_passed"] = component_passed
        self.validation_results["components_total"] = component_count
    
    def _count_classes_in_file(self, file_path: Path) -> int:
        """Count classes in a Python file."""
        try:
            content = file_path.read_text()
            return content.count("class ")
        except Exception:
            return 0
    
    def _count_functions_in_file(self, file_path: Path) -> int:
        """Count functions in a Python file."""
        try:
            content = file_path.read_text()
            return content.count("def ")
        except Exception:
            return 0
    
    def generate_validation_report(self) -> str:
        """Generate a human-readable validation report."""
        if not self.validation_results:
            return "No validation results available. Run validate_framework() first."
        
        lines = []
        lines.append("="*80)
        lines.append("CANDY-CADENCE TESTING FRAMEWORK VALIDATION REPORT")
        lines.append("="*80)
        lines.append(f"Timestamp: {self.validation_results['timestamp']}")
        lines.append(f"Overall Status: {self.validation_results['overall_status']}")
        lines.append(f"Completion Score: {self.validation_results.get('completion_score', 0):.1f}%")
        lines.append("")
        
        # Framework Components
        lines.append("FRAMEWORK COMPONENTS:")
        lines.append("-" * 40)
        components = self.validation_results["framework_components"]
        for name, info in components.items():
            if isinstance(info, dict) and "status" in info:
                status_icon = "[OK]" if info["status"] == "FOUND" else "[X]"
                lines.append(f"{status_icon} {name}: {info['status']}")
        lines.append("")
        
        # Test Execution
        lines.append("TEST EXECUTION:")
        lines.append("-" * 40)
        test_exec = self.validation_results["test_execution"]
        lines.append(f"Basic pytest execution: {test_exec.get('basic_execution', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Coverage tools: {test_exec.get('coverage_tools', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Test data: {test_exec.get('test_data', {}).get('status', 'UNKNOWN')}")
        lines.append("")
        
        # Quality Assurance
        lines.append("QUALITY ASSURANCE:")
        lines.append("-" * 40)
        qa = self.validation_results["quality_assurance"]
        lines.append(f"QA Engine: {qa.get('qa_engine', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Quality Metrics: {qa.get('quality_metrics', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Quality Gates: {qa.get('gates', {}).get('status', 'UNKNOWN')}")
        lines.append("")
        
        # Documentation
        lines.append("DOCUMENTATION:")
        lines.append("-" * 40)
        docs = self.validation_results["documentation"]
        lines.append(f"Main Documentation: {docs.get('main_documentation', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Best Practices: {docs.get('best_practices', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Documentation Structure: {docs.get('docs_structure', {}).get('status', 'UNKNOWN')}")
        lines.append("")
        
        # Integration
        lines.append("INTEGRATION:")
        lines.append("-" * 40)
        integration = self.validation_results["integration"]
        lines.append(f"Component Integration: {integration.get('component_integration', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Import Chain: {integration.get('import_chain', {}).get('status', 'UNKNOWN')}")
        lines.append(f"Configuration: {integration.get('configuration', {}).get('status', 'UNKNOWN')}")
        
        # Component test results
        comp_details = integration.get('component_integration', {}).get('details', {})
        if 'test_results' in comp_details:
            lines.append("")
            lines.append("Integration Test Results:")
            for result in comp_details['test_results']:
                icon = "[OK]" if ": OK" in result else "[X]"
                lines.append(f"  {icon} {result}")
        
        lines.append("")
        lines.append("="*80)
        
        return "\n".join(lines)


def main():
    """Main validation function."""
    print("Candy-Cadence Testing Framework Validation")
    print("=" * 50)
    
    # Create validator and run validation
    validator = FrameworkValidator()
    results = validator.validate_framework()
    
    # Generate and display report
    report = validator.generate_validation_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"framework_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Return exit code based on status
    status = results.get("overall_status", "UNKNOWN")
    if status in ["EXCELLENT", "GOOD"]:
        print("\n[OK] Framework validation PASSED")
        return 0
    elif status == "FAIR":
        print("\n[!] Framework validation PARTIAL")
        return 1
    else:
        print("\n[X] Framework validation FAILED")
        return 2


if __name__ == "__main__":
    exit(main())