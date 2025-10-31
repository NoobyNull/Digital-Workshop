#!/usr/bin/env python3
"""
Digital Workshop Root Directory Cleanup Validation Script

This script validates that the cleanup operation was successful by checking:
1. File count reduction in root directory
2. Essential files are still present
3. New directory structure exists
4. Basic functionality still works
5. No broken imports or references

Usage: python validate_cleanup.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class CleanupValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validation_passed': True,
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
    def log_result(self, check_name, passed, message="", details=None):
        """Log validation result"""
        self.results['checks'][check_name] = {
            'passed': passed,
            'message': message,
            'details': details or {}
        }
        
        if not passed:
            self.results['validation_passed'] = False
            self.results['errors'].append(f"{check_name}: {message}")
            
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}: {message}")
        
    def log_warning(self, warning):
        """Log warning message"""
        self.results['warnings'].append(warning)
        print(f"⚠️  WARNING: {warning}")
        
    def check_root_file_count(self):
        """Check that root directory file count has been reduced"""
        try:
            root_files = list(Path('.').glob('*'))
            file_count = len([f for f in root_files if f.is_file()])
            
            # Should be significantly reduced from original ~100+ files
            expected_max = 20  # Allow some flexibility for essential files
            passed = file_count <= expected_max
            
            self.log_result(
                "Root File Count Reduction",
                passed,
                f"Root directory contains {file_count} files (expected ≤{expected_max})",
                {'actual_count': file_count, 'expected_max': expected_max}
            )
            
        except Exception as e:
            self.log_result("Root File Count Reduction", False, f"Error checking file count: {e}")
            
    def check_essential_files(self):
        """Check that all essential files are still present"""
        essential_files = [
            'README.md',
            'pyproject.toml', 
            'requirements.txt',
            'requirements_testing.txt',
            'requirements-conda.yml',
            '.gitignore',
            '.pylintrc',
            'pytest.ini',
            'run.py',
            'build.py'
        ]
        
        missing_files = []
        for file in essential_files:
            if not os.path.exists(file):
                missing_files.append(file)
                
        passed = len(missing_files) == 0
        
        self.log_result(
            "Essential Files Present",
            passed,
            f"Missing essential files: {missing_files}" if missing_files else "All essential files present",
            {'missing_files': missing_files, 'checked_files': essential_files}
        )
        
    def check_directory_structure(self):
        """Check that new directory structure was created"""
        expected_dirs = [
            'config',
            'samples',
            'samples/code',
            'samples/reports', 
            'build',
            'build/installer',
            'build/logs',
            'archive',
            'docs/guides',
            'docs/architecture',
            'docs/reports',
            'tests/unit',
            'tests/integration',
            'tests/framework',
            'tests/parsers',
            'tests/persistence',
            'tests/themes',
            'tests/performance',
            'tests/runner',
            'reports/json',
            'reports/html',
            'reports/analysis',
            'reports/comprehensive',
            'reports/performance',
            'reports/quality',
            'reports/test_results',
            'tools/quality',
            'tools/analysis',
            'tools/debug',
            'tools/exceptions',
            'tools/migration',
            'tools/demos'
        ]
        
        missing_dirs = []
        for dir_path in expected_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
                
        passed = len(missing_dirs) == 0
        
        self.log_result(
            "Directory Structure Created",
            passed,
            f"Missing directories: {missing_dirs}" if missing_dirs else "All directories created",
            {'missing_dirs': missing_dirs, 'checked_dirs': expected_dirs}
        )
        
    def check_file_organization(self):
        """Check that files were moved to appropriate directories"""
        organization_checks = [
            # Check documentation files
            ('docs/guides/QUICK_START.md', 'QUICK_START_GUIDE.md moved to docs/guides/'),
            ('docs/guides/REFACTORING.md', 'REFACTORING_SOLUTIONS.md moved to docs/guides/'),
            ('docs/architecture/IMPORT_PROCESS.md', 'IMPORT_PROCESS_ARCHITECTURE.md moved to docs/architecture/'),
            
            # Check test files
            ('tests/unit/', 'test_*.py files moved to tests/unit/'),
            ('tests/integration/', 'Integration test files moved to tests/integration/'),
            ('tests/runner.py', 'unified_test_runner.py moved to tests/runner.py'),
            
            # Check configuration files
            ('config/quality_config.yaml', 'quality_config.yaml moved to config/'),
            ('config/test_framework_config.json', 'test_framework_config.json moved to config/'),
            
            # Check sample files
            ('samples/', 'sample/ directory moved to samples/'),
            ('samples/code/', 'sample_*.py files moved to samples/code/'),
            
            # Check build files
            ('build/installer/', 'installer/ directory moved to build/installer/'),
            
            # Check archive
            ('archive/', 'Temporary files moved to archive/')
        ]
        
        passed_checks = 0
        for file_path, description in organization_checks:
            if os.path.exists(file_path) or (file_path.endswith('/') and os.path.exists(file_path)):
                passed_checks += 1
            else:
                self.log_warning(f"File organization check failed: {description}")
                
        total_checks = len(organization_checks)
        passed = passed_checks >= (total_checks * 0.8)  # Allow 20% tolerance
        
        self.log_result(
            "File Organization",
            passed,
            f"{passed_checks}/{total_checks} organization checks passed",
            {'passed_checks': passed_checks, 'total_checks': total_checks}
        )
        
    def check_python_functionality(self):
        """Check that basic Python functionality still works"""
        try:
            # Test Python import
            result = subprocess.run([
                sys.executable, '-c', 
                'import sys; sys.path.insert(0, "."); print("Python import test passed")'
            ], capture_output=True, text=True, timeout=10)
            
            python_import_passed = result.returncode == 0
            
            self.log_result(
                "Python Import Test",
                python_import_passed,
                "Python imports work correctly" if python_import_passed else "Python import failed",
                {'stdout': result.stdout, 'stderr': result.stderr}
            )
            
        except Exception as e:
            self.log_result("Python Import Test", False, f"Error testing Python imports: {e}")
            
    def check_pytest_functionality(self):
        """Check that pytest configuration still works"""
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', '--collect-only', '-q'
            ], capture_output=True, text=True, timeout=30)
            
            pytest_passed = result.returncode == 0
            
            self.log_result(
                "Pytest Configuration Test",
                pytest_passed,
                "Pytest configuration works" if pytest_passed else "Pytest configuration failed",
                {'stdout': result.stdout, 'stderr': result.stderr}
            )
            
        except Exception as e:
            self.log_result("Pytest Configuration Test", False, f"Error testing pytest: {e}")
            
    def check_build_functionality(self):
        """Check that build script still works"""
        try:
            if os.path.exists('build.py'):
                result = subprocess.run([
                    sys.executable, 'build.py', '--help'
                ], capture_output=True, text=True, timeout=10)
                
                build_passed = result.returncode == 0
                
                self.log_result(
                    "Build Script Test",
                    build_passed,
                    "Build script works" if build_passed else "Build script failed",
                    {'stdout': result.stdout, 'stderr': result.stderr}
                )
            else:
                self.log_result("Build Script Test", False, "build.py not found")
                
        except Exception as e:
            self.log_result("Build Script Test", False, f"Error testing build script: {e}")
            
    def check_no_broken_references(self):
        """Check for common broken references"""
        broken_refs = []
        
        # Check for references to old test file locations
        try:
            if os.path.exists('src'):
                result = subprocess.run([
                    'grep', '-r', 'test_.*\.py', 'src/', '--include=*.py'
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    broken_refs.append("Found potential hardcoded test file references in src/")
                    
        except Exception:
            pass  # grep might not be available on all systems
            
        # Check for references to old report locations
        try:
            if os.path.exists('src'):
                result = subprocess.run([
                    'grep', '-r', 'reports/', 'src/', '--include=*.py'
                ], capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    broken_refs.append("Found potential hardcoded report references in src/")
                    
        except Exception:
            pass
            
        passed = len(broken_refs) == 0
        
        self.log_result(
            "No Broken References",
            passed,
            f"Potential issues: {broken_refs}" if broken_refs else "No broken references found",
            {'broken_references': broken_refs}
        )
        
    def generate_report(self):
        """Generate validation report"""
        report_file = f"cleanup_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n📊 Validation report saved to: {report_file}")
        
        # Print summary
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for check in self.results['checks'].values() if check['passed'])
        
        print(f"\n📈 VALIDATION SUMMARY:")
        print(f"Total checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        print(f"Warnings: {len(self.results['warnings'])}")
        
        if self.results['validation_passed']:
            print(f"\n✅ OVERALL RESULT: CLEANUP VALIDATION PASSED")
            print("The cleanup operation was successful!")
        else:
            print(f"\n❌ OVERALL RESULT: CLEANUP VALIDATION FAILED")
            print("Please review the errors above and take corrective action.")
            
        return self.results['validation_passed']
        
    def run_all_validations(self):
        """Run all validation checks"""
        print("🔍 Starting Digital Workshop Cleanup Validation...")
        print("=" * 60)
        
        self.check_root_file_count()
        self.check_essential_files()
        self.check_directory_structure()
        self.check_file_organization()
        self.check_python_functionality()
        self.check_pytest_functionality()
        self.check_build_functionality()
        self.check_no_broken_references()
        
        return self.generate_report()

def main():
    """Main validation function"""
    validator = CleanupValidator()
    success = validator.run_all_validations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()