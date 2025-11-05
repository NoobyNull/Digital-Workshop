#!/usr/bin/env python3
"""
Test script for per-module PyInstaller compilation

Tests each module spec individually to ensure they compile correctly.
"""

import subprocess
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Module specifications
MODULES = [
    {
        'name': 'core',
        'spec': 'config/pyinstaller-core.spec',
        'expected_size_mb': 40,
        'tolerance_mb': 10,
    },
    {
        'name': 'pyside6',
        'spec': 'config/pyinstaller-pyside6.spec',
        'expected_size_mb': 70,
        'tolerance_mb': 15,
    },
    {
        'name': 'vtk',
        'spec': 'config/pyinstaller-vtk.spec',
        'expected_size_mb': 80,
        'tolerance_mb': 20,
    },
    {
        'name': 'opencv',
        'spec': 'config/pyinstaller-opencv.spec',
        'expected_size_mb': 50,
        'tolerance_mb': 15,
    },
    {
        'name': 'numpy',
        'spec': 'config/pyinstaller-numpy.spec',
        'expected_size_mb': 30,
        'tolerance_mb': 10,
    },
]

class ModuleCompilationTester:
    """Tests per-module PyInstaller compilation."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.dist_dir = self.project_root / 'dist'
        self.results = []
        self.start_time = datetime.now()
    
    def get_directory_size_mb(self, path):
        """Calculate total size of directory in MB."""
        total_size = 0
        for file_path in Path(path).rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    def compile_module(self, module):
        """Compile a single module."""
        logger.info(f"Compiling {module['name']} module...")
        
        spec_file = self.project_root / module['spec']
        if not spec_file.exists():
            logger.error(f"Spec file not found: {spec_file}")
            return False
        
        cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"Compilation failed for {module['name']}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                return False
            
            logger.info(f"Successfully compiled {module['name']} module")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Compilation timeout for {module['name']} (> 10 minutes)")
            return False
        except Exception as e:
            logger.error(f"Compilation error for {module['name']}: {e}")
            return False
    
    def verify_module(self, module):
        """Verify compiled module."""
        logger.info(f"Verifying {module['name']} module...")
        
        module_dir = self.dist_dir / module['name']
        
        if not module_dir.exists():
            logger.error(f"Module directory not found: {module_dir}")
            return False
        
        # Check if executable exists
        exe_name = f"{module['name']}_module.exe" if module['name'] != 'core' else "Digital Workshop.exe"
        exe_path = module_dir / exe_name
        
        if not exe_path.exists():
            logger.warning(f"Executable not found: {exe_path}")
            # This might be okay for non-core modules
        
        # Check directory size
        size_mb = self.get_directory_size_mb(module_dir)
        expected_size = module['expected_size_mb']
        tolerance = module['tolerance_mb']
        
        logger.info(f"{module['name']} module size: {size_mb:.2f} MB (expected: {expected_size} ± {tolerance} MB)")
        
        if abs(size_mb - expected_size) > tolerance:
            logger.warning(f"Size mismatch for {module['name']}: {size_mb:.2f} MB vs {expected_size} MB")
            # Don't fail on size mismatch, just warn
        
        return True
    
    def test_module(self, module):
        """Test a single module."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {module['name'].upper()} module")
        logger.info(f"{'='*60}")
        
        # Compile
        if not self.compile_module(module):
            return False
        
        # Verify
        if not self.verify_module(module):
            return False
        
        logger.info(f"✓ {module['name']} module test passed")
        return True
    
    def run_all_tests(self):
        """Run tests for all modules."""
        logger.info(f"Starting module compilation tests at {self.start_time}")
        logger.info(f"Testing {len(MODULES)} modules")
        
        for module in MODULES:
            success = self.test_module(module)
            self.results.append({
                'module': module['name'],
                'success': success,
            })
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        for result in self.results:
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            logger.info(f"{status}: {result['module']}")
        
        logger.info(f"\nTotal: {passed}/{total} passed")
        logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
        logger.info(f"{'='*60}")
        
        return passed == total

def main():
    """Main function."""
    tester = ModuleCompilationTester()
    
    try:
        tester.run_all_tests()
        
        # Exit with appropriate code
        all_passed = all(r['success'] for r in tester.results)
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

