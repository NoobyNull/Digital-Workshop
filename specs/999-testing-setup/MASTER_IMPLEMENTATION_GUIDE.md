
# Master Implementation Guide: Comprehensive Testing Framework

**Date**: 2025-10-31 | **Version**: 1.0 | **Status**: Ready for Implementation

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites and Dependencies](#prerequisites-and-dependencies)
3. [Installation and Configuration](#installation-and-configuration)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Usage Examples and Best Practices](#usage-examples-and-best-practices)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Integration with Existing Workflow](#integration-with-existing-workflow)

## Overview

This guide provides comprehensive instructions for implementing the four-component testing framework:

1. **Code Formatting and Linting Validator** - Ensures 95.56% compliance through Black and Pylint
2. **Monolithic Module Detector** - Identifies modules exceeding 500 lines
3. **File Naming Convention Validator** - Eliminates descriptive adjectives in filenames
4. **Unified Test Execution System** - Centralized test execution and reporting

## Prerequisites and Dependencies

### System Requirements

**Minimum Requirements:**
- Python 3.8 or higher
- 4GB RAM
- 1GB free disk space
- Git for version control

**Recommended Requirements:**
- Python 3.9-3.12
- 8GB RAM
- SSD storage
- Multi-core CPU (4+ cores)

### Required Python Packages

```bash
# Core testing framework
pytest>=7.0.0
pytest-xdist>=3.0.0
pytest-cov>=4.0.0
pytest-html>=3.0.0
pytest-json-report>=1.5.0
pytest-timeout>=2.0.0

# Code quality tools
black>=22.0.0
pylint>=2.15.0
isort>=5.10.0
mypy>=1.0.0
bandit>=1.7.0

# Data processing and utilities
pathlib2>=2.3.0
dataclasses-json>=0.5.0
jsonschema>=4.0.0
```

### Optional Dependencies

```bash
# Advanced reporting
allure-pytest>=2.13.0
pytest-benchmark>=4.0.0

# Performance monitoring
memory-profiler>=0.60.0
psutil>=5.9.0

# Natural language processing (for naming validation)
nltk>=3.8.0
```

## Installation and Configuration

### Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv testing_framework_env
source testing_framework_env/bin/activate  # Linux/Mac
# testing_framework_env\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Create requirements file
cat > requirements-testing.txt << EOF
pytest>=7.0.0
pytest-xdist>=3.0.0
pytest-cov>=4.0.0
pytest-html>=3.0.0
pytest-json-report>=1.5.0
pytest-timeout>=2.0.0
black>=22.0.0
pylint>=2.15.0
isort>=5.10.0
mypy>=1.0.0
bandit>=1.7.0
pathlib2>=2.3.0
dataclasses-json>=0.5.0
jsonschema>=4.0.0
EOF

# Install dependencies
pip install -r requirements-testing.txt
```

### Step 3: Project Structure Setup

```bash
# Create directory structure
mkdir -p tools/testing_framework/{src,tests,config,reports,scripts}
mkdir -p tools/testing_framework/src/{validators,executors,models,utils}
mkdir -p tools/testing_framework/tests/{unit,integration,e2e}
mkdir -p tools/testing_framework/reports/{html,json,xml}

# Create __init__.py files
touch tools/testing_framework/src/__init__.py
touch tools/testing_framework/src/validators/__init__.py
touch tools/testing_framework/src/executors/__init__.py
touch tools/testing_framework/src/models/__init__.py
touch tools/testing_framework/src/utils/__init__.py
```

### Step 4: Configuration Files

#### Create pytest.ini

```ini
# tools/testing_framework/config/pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:reports/coverage_html
    --cov-report=xml:reports/coverage.xml
    --junit-xml=reports/junit.xml
    --html=reports/pytest_report.html
    --self-contained-html

testpaths = tests

python_files = test_*.py *_test.py

python_classes = Test*

python_functions = test_*

markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interactions
    performance: Performance and load tests
    e2e: End-to-end workflow tests
    quality: Code quality and linting tests
    slow: Tests that take longer than 5 seconds
    fast: Tests that complete quickly

filterwarnings =
    ignore::UserWarning
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

timeout = 300

log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

log_file = reports/pytest.log
log_file_level = DEBUG
log_file_format = %(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d %(funcName)s(): %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
```

#### Create Black Configuration

```toml
# tools/testing_framework/config/.black.toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | \.pytest_cache
)/
'''
```

#### Create Pylint Configuration

```ini
# tools/testing_framework/config/.pylintrc
[MASTER]
jobs=0
persistent=yes
load-plugins=

[MESSAGES CONTROL]
disable=
    C0114,  # missing-module-docstring
    C0115,  # missing-class-docstring
    C0116,  # missing-function-docstring
    R0903,  # too-few-public-methods
    R0913,  # too-many-arguments
    W0613,  # unused-argument
    W0622,  # redefined-builtin
    R0801,  # duplicate-code

[FORMAT]
max-line-length=88
ignore-long-lines=^\s*(# )?<?https?://\S+>?$
single-line-if-stmt=no

[DESIGN]
max-args=7
max-attributes=15
max-bool-expr=5
max-branches=15
max-locals=20
max-parents=7
max-public-methods=25
max-returns=8
max-statements=60
min-public-methods=1

[SIMILARITIES]
min-similarity-lines=4
ignore-comments=yes
ignore-docstrings=yes
ignore-imports=no
```

## Step-by-Step Implementation

### Phase 1: Core Data Model Implementation

#### Step 1.1: Create Data Models

```python
# tools/testing_framework/src/models/entities.py
"""
Data model entities for the testing framework.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"

class Severity(Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NONE = "none"

@dataclass
class TestSuite:
    """TestSuite entity for unified test execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # unit, integration, performance, e2e, quality
    test_patterns: List[str] = field(default_factory=list)
    execution_config: Dict[str, Any] = field(default_factory=dict)
    quality_gates: List[Dict[str, Any]] = field(default_factory=list)
    schedule: Dict[str, Any] = field(default_factory=dict)
    status: TestStatus = TestStatus.PENDING
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class TestExecution:
    """TestExecution entity for recording execution results."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_suite_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    status: TestStatus = TestStatus.PENDING
    exit_code: int = 0
    test_results: Dict[str, Any] = field(default_factory=dict)
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    logs: str = ""
    artifacts: List[str] = field(default_factory=list)
    quality_score: float = 0.0

@dataclass
class CodeQuality:
    """CodeQuality entity for formatting and linting results."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_path: str = ""
    analysis_type: str = ""  # lint, format, type_check, security
    tool_name: str = ""
    tool_version: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    overall_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    compliance_status: bool = False
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ModuleAnalysis:
    """ModuleAnalysis entity for architectural analysis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module_path: str = ""
    analysis_type: str = ""  # architecture, dependencies, complexity
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    module_metrics: Dict[str, Any] = field(default_factory=dict)
    architecture_violations: List[Dict[str, Any]] = field(default_factory=list)
    monolithic_indicators: Dict[str, bool] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    compliance_score: float = 0.0

@dataclass
class NamingConvention:
    """NamingConvention entity for naming validation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_path: str = ""
    convention_type: str = ""  # file, class, function, variable, constant
    naming_rules: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    compliance_percentage: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class QualityGate:
    """QualityGate entity for threshold enforcement."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    gate_type: str = ""  # coverage, performance, security, architecture
    metric_name: str = ""
    threshold_value: float = 0.0
    comparison_operator: str = ">"
    severity: Severity = Severity.MAJOR
    enabled: bool = True
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

### Phase 2: Individual Tool Implementation

#### Step 2.1: Code Formatting and Linting Validator

```python
# tools/testing_framework/src/validators/code_quality_validator.py
"""
Code Formatting and Linting Validator Implementation
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from ..models.entities import CodeQuality

@dataclass
class FormattingResult:
    """Results from Black formatting validation."""
    file_path: str
    was_formatted: bool
    original_size: int
    formatted_size: int
    changes_made: List[str]
    processing_time: float
    error_message: Optional[str] = None

@dataclass
class LintingIssue:
    """Individual linting issue from Pylint."""
    file_path: str
    line_number: int
    column: int
    issue_type: str
    symbol: str
    message: str
    confidence: str

@dataclass
class LintingResult:
    """Results from Pylint analysis."""
    file_path: str
    overall_score: float
    issues: List[LintingIssue]
    rating: str
    processing_time: float
    error_message: Optional[str] = None

@dataclass
class ComplianceResult:
    """Overall compliance result."""
    target_compliance: float
    actual_compliance: float
    formatting_score: float
    linting_score: float
    overall_score: float
    passed: bool
    violations: List[str]
    recommendations: List[str]

class CodeQualityValidator:
    """Main validator for code formatting and linting."""
    
    def __init__(self, target_compliance: float = 95.56):
        self.target_compliance = target_compliance
        self.black_config = self._get_black_config()
        self.pylint_config = self._get_pylint_config()
        
    def _get_black_config(self) -> Dict[str, Any]:
        """Get Black configuration."""
        return {
            "line_length": 88,
            "target_version": ["py38"],
            "include": "\\.pyi?$",
            "extend_exclude": """
            /(
              \\.eggs
              | \\.git
              | \\.hg
              | \\.mypy_cache
              | \\.tox
              | \\.venv
              | build
              | dist
            )/
            """
        }
    
    def _get_pylint_config(self) -> Dict[str, Any]:
        """Get Pylint configuration."""
        return {
            "max_line_length": 88,
            "disable": [
                "C0114", "C0115", "C0116", "R0903", "R0913",
                "W0613", "W0622"
            ],
            "enable": [
                "E", "W", "F", "I", "C", "R"
            ]
        }
    
    def format_with_black(self, file_path: Path, fix_mode: bool = True) -> FormattingResult:
        """Format a file with Black."""
        start_time = time.time()
        
        try:
            original_size = file_path.stat().st_size if file_path.exists() else 0
            
            cmd = ["python", "-m", "black"]
            if fix_mode:
                cmd.append("--fix")
            else:
                cmd.append("--check")
            
            cmd.extend([
                "--line-length", str(self.black_config["line_length"]),
                "--target-version", self.black_config["target_version"][0],
                str(file_path)
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            formatted_size = file_path.stat().st_size if file_path.exists() else 0
            was_formatted = result.returncode != 0 if not fix_mode else len(result.stdout.strip()) > 0
            
            changes_made = []
            if was_formatted and fix_mode:
                changes_made = ["code formatting applied"]
            
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=was_formatted,
                original_size=original_size,
                formatted_size=formatted_size,
                changes_made=changes_made,
                processing_time=processing_time
            )
            
        except Exception as e:
            return FormattingResult(
                file_path=str(file_path),
                was_formatted=False,
                original_size=0,
                formatted_size=0,
                changes_made=[],
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def lint_with_pylint(self, file_path: Path) -> LintingResult:
        """Lint a file with Pylint."""
        start_time = time.time()
        
        try:
            cmd = [
                "python", "-m", "pylint",
                "--output-format", "json",
                "--score", "yes",
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            processing_time = time.time() - start_time
            
            issues = []
            overall_score = 10.0
            
            if result.stdout.strip():
                try:
                    pylint_output = json.loads(result.stdout)
                    
                    for issue_data in pylint_output:
                        issue = LintingIssue(
                            file_path=issue_data.get("path", str(file_path)),
                            line_number=issue_data.get("line", 0),
                            column=issue_data.get("column", 0),
                            issue_type=issue_data.get("type", "unknown"),
                            symbol=issue_data.get("symbol", ""),
                            message=issue_data.get("message", ""),
                            confidence=issue_data.get("confidence", "HIGH")
                        )
                        issues.append(issue)
                    
                    # Extract score from stderr
                    if result.stderr:
                        import re
                        score_match = re.search(r"rated at ([0-9.]+)/10", result.stderr)
                        if score_match:
                            overall_score = float(score_match.group(1))
                            
                except json.JSONDecodeError:
                    logging.warning(f"Failed to parse Pylint JSON output for {file_path}")
            
            if overall_score >= 9.0:
                rating = "Excellent"
            elif overall_score >= 7.5:
                rating = "Good"
            elif overall_score >= 6.0:
                rating = "Acceptable"
            else:
                rating = "Poor"
            
            return LintingResult(
                file_path=str(file_path),
                overall_score=overall_score,
                issues=issues,
                rating=rating,
                processing_time=processing_time
            )
            
        except Exception as e:
            return LintingResult(
                file_path=str(file_path),
                overall_score=0.0,
                issues=[],
                rating="Poor",
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def validate_file(self, file_path: Path, fix_formatting: bool = True) -> Tuple[FormattingResult, LintingResult]:
        """Validate a single file for formatting and linting."""
        logging.info(f"Validating {file_path}")
        
        formatting_result = self.format_with_black(file_path, fix_formatting)
        linting_result = self.lint_with_pylint(file_path)
        
        return formatting_result, linting_result
    
    def calculate_compliance(self, results: List[Tuple[FormattingResult, LintingResult]]) -> ComplianceResult:
        """Calculate overall compliance score."""
        if not results:
            return ComplianceResult(
                target_compliance=self.target_compliance,
                actual_compliance=0.0,
                formatting_score=0.0,
                linting_score=0.0,
                overall_score=0.0,
                passed=False,
                violations=["No files to validate"],
                recommendations=["Add Python files to validate"]
            )
        
        # Calculate formatting score
        formatting_scores = []
        for formatting_result, _ in results:
            if formatting_result.error_message:
                formatting_scores.append(0.0)
            else:
                score = 100.0 if not formatting_result.was_formatted else 85.0
                formatting_scores.append(score)
        
        formatting_score = sum(formatting_scores) / len(formatting_scores)
        
        # Calculate linting score
        linting_scores = []
        total_issues = 0
        critical_issues = 0
        
        for _, linting_result in results:
            if linting_result.error_message:
                linting_scores.append(0.0)
            else:
                score = linting_result.overall_score * 10.0
                linting_scores.append(score)
                total_issues += len(linting_result.issues)
                critical_issues += len([i for i in linting_result.issues if i.issue_type == "error"])
        
        linting_score = sum(linting_scores) / len(linting_scores)
        
        # Calculate overall score (weighted average)
        overall_score = (formatting_score * 0.3 + linting_score * 0.7)
        
        # Determine compliance
        actual_compliance = overall_score
        passed = actual_compliance >= self.target_compliance
        
        # Generate violations and recommendations
        violations = []
        recommendations = []
        
        if not passed:
            violations.append(f"Compliance {actual_compliance:.2f}% is below target {self.target_compliance}%")
        
        if formatting_score < 90.0:
            violations.append(f"Formatting score {formatting_score:.2f}% is below 90%")
            recommendations.append("Run Black formatter to fix formatting issues")
        
        if linting_score < 90.0:
            violations.append(f"Linting score {linting_score:.2f}% is below 90%")
            recommendations.append("Address Pylint warnings and errors")
        
        if critical_issues > 0:
            violations.append(f"Found {critical_issues} critical linting errors")
            recommendations.append("Fix critical errors immediately")
        
        if not recommendations:
            recommendations.append("Code quality is excellent! Keep up the good work.")
        
        return ComplianceResult(
            target_compliance=self.target_compliance,
            actual_compliance=actual_compliance,
            formatting_score=formatting_score,
            linting_score=linting_score,
            overall_score=overall_score,
            passed=passed,
            violations=violations,
            recommendations=recommendations
        )
```

#### Step 2.2: Monolithic Module Detector

```python
# tools/testing_framework/src/validators/monolithic_detector.py
"""
Monolithic Module Detector Implementation
"""

import ast
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.entities import ModuleAnalysis

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
        """Accurately count different types of lines in a Python file."""
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
            
            # Count comment lines
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
            logging.error(f"Error analyzing {file_path}: {e}")
            return {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'docstring_lines': 0,
                'blank_lines': 0
            }
    
    def analyze_file(self, file_path: Path) -> ModuleMetrics:
        """Analyze a single Python file for monolithic patterns."""
        logging.info(f"Analyzing {file_path}")
        
        line_counts = self.count_lines_accurate(file_path)
        code_lines = line_counts['code_lines']
        
        # Determine severity based on threshold excess
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
            timestamp=datetime.now().isoformat()
        )
    
    def scan_directory(self, root_path: Path) -> List[ModuleMetrics]:
        """Recursively scan directory for Python files and analyze them."""
        python_files = list(root_path.rglob('*.py'))
        logging.info(f"Found {len(python_files)} Python files to analyze")
        
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
                    logging.error(f"Failed to analyze {file_path}: {e}")
        
        return results
```

#### Step 2.3: File Naming Convention Validator

```python
# tools/testing_framework/src/validators/naming_validator.py
"""
File Naming Convention Validator Implementation
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.entities import NamingConvention

@dataclass
class NamingViolation:
    """Represents a naming convention violation."""
    file_path: str
    file_name: str
    detected_adjectives: List[str]
    violation_type: str
    severity: str
    suggested_name: str
    line_number: int = 0

@dataclass
class NamingValidationResult:
    """Results of naming convention validation."""
    total_files: int
    valid_files: int
    violated_files: int
    violations: List[NamingViolation]
    compliance_rate: float
    timestamp: str

class AdjectiveDetector:
    """Detects descriptive adjectives in filenames."""
    
    def __init__(self):
        # Comprehensive list of replacement/description adjectives
        self.replacement_adjectives = {
            'refactored', 'new', 'old', 'backup', 'temp', 'temporary',
            'original', 'copy', 'duplicate', 'alternative', 'alternate',
            'improved', 'enhanced', 'optimized', 'better', 'updated',
            'revised', 'modified', 'changed', 'fixed', 'corrected',
            'working', 'final', 'complete', 'incomplete', 'draft',
            'experimental', 'testing', 'debug', 'development', 'prod',
            'production', 'staging', 'beta', 'alpha', 'stable',
            'good', 'bad', 'best', 'worst', 'fast', 'slow',
            'recent', 'latest', 'current', 'previous', 'next',
            'v1', 'v2', 'v3', 'version1', 'version2', 'version3',
            'active', 'inactive', 'enabled', 'disabled', 'on', 'off',
            'simple', 'complex', 'basic', 'advanced', 'standard',
            'custom', 'special', 'generic', 'specific', 'general'
        }
        
        # Domain-specific terms that should NOT be flagged
        self.domain_terms = {
            'user', 'admin', 'system', 'network', 'database', 'api',
            'http', 'https', 'ftp', 'ssh', 'tcp', 'udp', 'ip',
            'file', 'folder', 'directory', 'path', 'url', 'uri',
            'customer', 'product', 'order', 'invoice', 'payment',
            'main', 'app', 'core', 'base', 'common', 'shared',
            'model', 'view', 'controller', 'entity', 'record'
        }
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        adjective_pattern = r'\b(' + '|'.join(re.escape(word) for word in self.replacement_adjectives) + r')\b'
        self.adjective_regex = re.compile(adjective_pattern, re.IGNORECASE)
        
        compound_pattern = r'\b(' + '|'.join(re.escape(word) for word in self.replacement_adjectives) + r')_[a-zA-Z0-9_]+'
        self.compound_regex = re.compile(compound_pattern, re.IGNORECASE)
    
    def detect_adjectives(self, filename: str) -> List[str]:
        """Detect descriptive adjectives in a filename."""
        detected = []
        base_name = Path(filename).stem
        
        # Check for simple adjective matches
        simple_matches = self.adjective_regex.findall(base_name)
        detected.extend(simple_matches)
        
        # Check for compound word matches
        compound_matches = self.compound_regex.findall(base_name)
        detected.extend(compound_matches)
        
        return list(set(detected))
    
    def is_domain_term(self, word: str) -> bool:
        """Check if a word is a legitimate domain term."""
        return word.lower() in self.domain_terms
    
    def suggest_improved_name(self, filename: str, detected_adjectives: List[str]) -> str:
        """Suggest an improved filename without descriptive adjectives."""
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        improved_name = base_name
        for adjective in detected_adjectives:
            pattern = rf'\b{re.escape(adjective)}_?'
            improved_name = re.sub(pattern, '', improved_name, flags=re.IGNORECASE)
        
        improved_name = re.sub(r'_+', '_', improved_name).strip('_')
        
        if not improved_name or len(improved_name) < 3:
            improved_name = "component"
        
        return improved_name + extension

class NamingConventionValidator:
    """Main validator class for naming conventions."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.detector = AdjectiveDetector()
        self.results: List[NamingViolation] = []
        
    def validate_filename(self, file_path: Path) -> NamingViolation:
        """Validate a single filename for naming convention