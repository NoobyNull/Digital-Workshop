# Test Plan: Monolithic Module Detection

**Date**: 2025-10-31 | **Status**: Ready for Implementation | **Phase**: Phase 1

## Objective

Detect and flag Python modules that exceed 500 lines of code (excluding comments and docstrings) to identify potential monolithic architecture patterns and enforce modular design principles.

## Approach

### Technical Implementation Strategy

1. **Static Code Analysis**: Use Python AST (Abstract Syntax Tree) parsing to accurately count lines of code while excluding comments, docstrings, and blank lines
2. **Recursive Directory Scanning**: Implement breadth-first search to analyze all Python files in the codebase
3. **Threshold-Based Classification**: Flag modules exceeding the 500-line threshold with severity levels
4. **Integration with Existing Architecture**: Leverage the ModuleAnalysis entity from the data model

### Tools and Libraries

- **ast**: Built-in Python AST module for accurate code parsing
- **pathlib**: For cross-platform file system operations
- **json**: For structured logging and reporting
- **typing**: For type annotations and better code documentation
- **concurrent.futures**: For parallel processing of large codebases

## Test Cases

### Test Case 1: Basic Monolithic Detection
**Objective**: Verify detection of modules exceeding 500 lines

**Setup**:
```python
# Create test files with varying line counts
small_module.py      # 50 lines
medium_module.py     # 300 lines  
large_module.py      # 600 lines (should be flagged)
monolithic_module.py # 1200 lines (should be flagged)
```

**Expected Results**:
- small_module.py: PASS (50 < 500)
- medium_module.py: PASS (300 < 500)
- large_module.py: FAIL (600 > 500)
- monolithic_module.py: FAIL (1200 > 500)

### Test Case 2: Comment and Docstring Exclusion
**Objective**: Ensure comments and docstrings don't count toward line totals

**Setup**:
```python
# test_module_with_comments.py
"""
This is a module docstring
Multiple lines
"""

# Single line comment
def function1():
    """Function docstring"""
    pass  # Inline comment

# Multiple comment lines
# Line 2
# Line 3
def function2():
    pass
```

**Expected Results**: 
- Total lines: 15
- Code lines: 4 (def function1, pass, def function2, pass)
- Should PASS if code lines < 500

### Test Case 3: Multi-line Statements Handling
**Objective**: Correctly handle multi-line statements and complex expressions

**Setup**:
```python
# test_multiline.py
data = [
    item1, item2, item3,
    item4, item5, item6,
    item7, item8, item9
]

def complex_function(
    param1,
    param2,
    param3=None
):
    return (
        param1 + param2 +
        param3 if param3 else 0
    )
```

**Expected Results**: 
- Correctly count logical lines, not physical lines
- Multi-line constructs should be counted appropriately

### Test Case 4: Performance with Large Codebases
**Objective**: Ensure efficient processing of large codebases

**Setup**:
- Create 1000+ Python files with varying sizes
- Measure processing time and memory usage

**Expected Results**:
- Processing time < 30 seconds for typical codebase
- Memory usage < 500MB
- Progress reporting for long operations

### Test Case 5: Integration with ModuleAnalysis Entity
**Objective**: Verify integration with the data model

**Setup**:
- Run detection on existing codebase
- Generate ModuleAnalysis entities
- Verify data model compliance

**Expected Results**:
- Proper ModuleAnalysis entity creation
- Correct monolithic_indicators population
- Accurate compliance_score calculation

## Implementation Code

### Core Detection Script

```python
#!/usr/bin/env python3
"""
Monolithic Module Detection Tool

Analyzes Python source code to identify modules exceeding
the specified line count threshold.
"""

import ast
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ModuleMetrics:
    """Metrics for a single module analysis."""
    path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    docstring_lines: int
    blank_lines: int
    is_monolithic: bool
    severity: str
    timestamp: str

class MonolithicDetector:
    """Main detector class for monolithic module identification."""
    
    def __init__(self, threshold: int = 500, max_workers: int = 4):
        self.threshold = threshold
        self.max_workers = max_workers
        self.results: List[ModuleMetrics] = []
        
    def count_lines_accurate(self, file_path: Path) -> Dict[str, int]:
        """
        Accurately count different types of lines in a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary with line counts by type
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse AST to get accurate line counts
            tree = ast.parse(content, filename=str(file_path))
            
            # Count lines using AST nodes
            code_lines = set()
            docstring_lines = set()
            
            for node in ast.walk(tree):
                if hasattr(node, 'lineno'):
                    code_lines.add(node.lineno)
                    
                # Check for docstrings
                if (isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)) and
                    node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    docstring_start = node.body[0].lineno
                    docstring_end = node.body[0].end_lineno or docstring_start
                    docstring_lines.update(range(docstring_start, docstring_end + 1))
            
            total_lines = len(content.splitlines())
            blank_lines = sum(1 for line in content.splitlines() 
                            if line.strip() == '')
            
            # Count comment lines (lines starting with #)
            comment_lines = 0
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith('#') and i not in code_lines:
                    comment_lines += 1
            
            actual_code_lines = len(code_lines) - len(docstring_lines)
            
            return {
                'total_lines': total_lines,
                'code_lines': actual_code_lines,
                'comment_lines': comment_lines,
                'docstring_lines': len(docstring_lines),
                'blank_lines': blank_lines
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'docstring_lines': 0,
                'blank_lines': 0
            }
    
    def analyze_file(self, file_path: Path) -> ModuleMetrics:
        """
        Analyze a single Python file for monolithic patterns.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            ModuleMetrics object with analysis results
        """
        logger.info(f"Analyzing {file_path}")
        
        line_counts = self.count_lines_accurate(file_path)
        code_lines = line_counts['code_lines']
        
        # Determine severity based on how much threshold is exceeded
        if code_lines > self.threshold:
            excess_ratio = code_lines / self.threshold
            if excess_ratio > 2.0:
                severity = 'critical'
            elif excess_ratio > 1.5:
                severity = 'major'
            else:
                severity = 'minor'
        else:
            severity = 'none'
        
        return ModuleMetrics(
            path=str(file_path),
            total_lines=line_counts['total_lines'],
            code_lines=code_lines,
            comment_lines=line_counts['comment_lines'],
            docstring_lines=line_counts['docstring_lines'],
            blank_lines=line_counts['blank_lines'],
            is_monolithic=code_lines > self.threshold,
            severity=severity,
            timestamp=__import__('datetime').datetime.now().isoformat()
        )
    
    def scan_directory(self, root_path: Path) -> List[ModuleMetrics]:
        """
        Recursively scan directory for Python files and analyze them.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            List of ModuleMetrics for all analyzed files
        """
        python_files = list(root_path.rglob('*.py'))
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        results = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.analyze_file, file_path): file_path 
                for file_path in python_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Failed to analyze {file_path}: {e}")
        
        return results
    
    def generate_report(self, results: List[ModuleMetrics]) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.
        
        Args:
            results: List of ModuleMetrics objects
            
        Returns:
            Dictionary containing the analysis report
        """
        total_files = len(results)
        monolithic_files = [r for r in results if r.is_monolithic]
        
        report = {
            'summary': {
                'total_files_analyzed': total_files,
                'monolithic_files_found': len(monolithic_files),
                'compliance_rate': ((total_files - len(monolithic_files)) / total_files * 100) 
                                 if total_files > 0 else 100,
                'threshold': self.threshold,
                'analysis_timestamp': __import__('datetime').datetime.now().isoformat()
            },
            'violations': [
                {
                    'path': result.path,
                    'code_lines': result.code_lines,
                    'severity': result.severity,
                    'excess_lines': result.code_lines - self.threshold
                }
                for result in monolithic_files
            ],
            'detailed_results': [asdict(result) for result in results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: Path):
        """
        Save analysis report to JSON file.
        
        Args:
            report: Analysis report dictionary
            output_path: Path to save the report
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for the monolithic detection tool."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect monolithic Python modules exceeding line thresholds'
    )
    parser.add_argument(
        'path', 
        help='Directory or file path to analyze'
    )
    parser.add_argument(
        '--threshold', 
        type=int, 
        default=500,
        help='Line count threshold (default: 500)'
    )
    parser.add_argument(
        '--output', 
        type=str,
        default='monolithic_analysis_report.json',
        help='Output report file path'
    )
    parser.add_argument(
        '--workers', 
        type=int,
        default=4,
        help='Number of worker threads (default: 4)'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = MonolithicDetector(threshold=args.threshold, max_workers=args.workers)
    
    # Analyze target path
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"Path does not exist: {target_path}")
        sys.exit(1)
    
    logger.info(f"Starting monolithic analysis of {target_path}")
    
    if target_path.is_file():
        results = [detector.analyze_file(target_path)]
    else:
        results = detector.scan_directory(target_path)
    
    # Generate and save report
    report = detector.generate_report(results)
    detector.save_report(report, Path(args.output))
    
    # Print summary
    print(f"\n=== Monolithic Module Detection Summary ===")
    print(f"Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Monolithic files found: {report['summary']['monolithic_files_found']}")
    print(f"Compliance rate: {report['summary']['compliance_rate']:.2f}%")
    
    if report['violations']:
        print(f"\nViolations found:")
        for violation in report['violations']:
            print(f"  - {violation['path']}: {violation['code_lines']} lines "
                  f"({violation['severity']} severity)")
    
    return 0 if report['summary']['monolithic_files_found'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
```

## Success Criteria

### Functional Requirements
- [ ] Accurately count code lines excluding comments and docstrings
- [ ] Process Python files recursively from specified directory
- [ ] Flag modules exceeding 500 lines with appropriate severity levels
- [ ] Generate structured JSON reports with detailed metrics
- [ ] Support parallel processing for large codebases
- [ ] Handle edge cases (empty files, syntax errors, encoding issues)

### Performance Requirements
- [ ] Process typical codebase (< 1000 files) in under 30 seconds
- [ ] Memory usage stays below 500MB during analysis
- [ ] Provide progress feedback for long-running operations
- [ ] Support cancellation for lengthy analyses

### Quality Requirements
- [ ] 100% accuracy in line counting (verified against manual counts)
- [ ] Zero false positives for modules under threshold
- [ ] Proper error handling for malformed Python files
- [ ] Cross-platform compatibility (Windows, Linux, macOS)

### Integration Requirements
- [ ] Generate ModuleAnalysis entities compatible with data model
- [ ] Integrate with QualityGate system for automated enforcement
- [ ] Support CI/CD pipeline integration via exit codes
- [ ] Provide JSON output for programmatic consumption

## Integration

### CI/CD Pipeline Integration

```yaml
# .github/workflows/monolithic-detection.yml
name: Monolithic Module Detection

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  detect-monolithic:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run Monolithic Detection
      run: |
        python tools/monolithic_detector.py src/ --threshold 500 --output reports/monolithic_report.json
    
    - name: Upload Report
      uses: actions/upload-artifact@v3
      with:
        name: monolithic-analysis-report
        path: reports/monolithic_report.json
    
    - name: Check for Violations
      run: |
        python -c "
        import json
        with open('reports/monolithic_report.json') as f:
            report = json.load(f)
        if report['summary']['monolithic_files_found'] > 0:
            print('Monolithic modules detected!')
            exit(1)
        "
```

### Quality Gate Integration

```python
# Integration with QualityGate system
class MonolithicQualityGate:
    """Quality gate for monolithic module detection."""
    
    def __init__(self, threshold: int = 500):
        self.threshold = threshold
        self.gate_id = "monolithic-detection"
    
    def evaluate(self, analysis_results: List[ModuleMetrics]) -> QualityGateResult:
        """Evaluate if the codebase passes the monolithic detection gate."""
        violations = [r for r in analysis_results if r.is_monolithic]
        
        return QualityGateResult(
            gate_id=self.gate_id,
            passed=len(violations) == 0,
            violations=violations,
            compliance_rate=((len(analysis_results) - len(violations)) / 
                           len(analysis_results) * 100) if analysis_results else 100
        )
```

### Automated Fix Suggestions

```python
def generate_refactoring_suggestions(metrics: ModuleMetrics) -> List[str]:
    """Generate refactoring suggestions for monolithic modules."""
    suggestions = []
    
    if metrics.code_lines > 1000:
        suggestions.append("Consider splitting this module into multiple smaller modules")
        suggestions.append("Extract related functionality into separate classes or modules")
    
    if metrics.code_lines > 2000:
        suggestions.append("This module is extremely large and should be refactored immediately")
        suggestions.append("Consider using a plugin architecture or dependency injection")
    
    # Analyze function count for additional suggestions
    # (Would need to parse AST for function definitions)
    
    return suggestions
```

---

**Test Plan Status**: ✅ Complete  
**Ready for Implementation**: ✅ Yes  
**Next Phase**: Implementation and Integration Testing