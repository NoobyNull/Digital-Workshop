# Test Plan: File Naming Convention Validation

**Date**: 2025-10-31 | **Status**: Ready for Implementation | **Phase**: Phase 1

## Objective

Validate that no files have adjective-based names that describe replacement files (e.g., "refactored", "new", "old", "backup", "temp") to ensure clean, professional naming conventions and prevent technical debt accumulation.

## Approach

### Technical Implementation Strategy

1. **Linguistic Pattern Analysis**: Use comprehensive adjective detection algorithms to identify descriptive terms in filenames
2. **Regex Pattern Matching**: Implement robust pattern matching for common replacement file indicators
3. **Contextual Analysis**: Distinguish between legitimate technical terms and descriptive adjectives
4. **Integration with NamingConvention Entity**: Leverage the data model for structured validation results

### Tools and Libraries

- **re**: Built-in regex module for pattern matching
- **nltk**: Natural Language Toolkit for linguistic analysis
- **pathlib**: For cross-platform file system operations
- **json**: For structured logging and reporting
- **typing**: For type annotations and better code documentation
- **concurrent.futures**: For parallel processing of large codebases

## Test Cases

### Test Case 1: Basic Adjective Detection
**Objective**: Detect common replacement file adjectives

**Setup**:
```python
# Create test files with various naming patterns
valid_file.py              # Should PASS
user_authentication.py     # Should PASS
data_processor.py          # Should PASS
refactored_parser.py       # Should FAIL (contains "refactored")
new_model_handler.py       # Should FAIL (contains "new")
old_viewer_widget.py       # Should FAIL (contains "old")
backup_config.py           # Should FAIL (contains "backup")
temp_solution.py           # Should FAIL (contains "temp")
```

**Expected Results**:
- Files without descriptive adjectives: PASS
- Files with replacement adjectives: FAIL with appropriate severity

### Test Case 2: Compound Adjective Detection
**Objective**: Handle compound words and variations

**Setup**:
```python
# Test compound adjectives and variations
improved_algorithm.py      # Should FAIL
enhanced_ui_component.py   # Should FAIL
optimized_renderer.py      # Should FAIL
modern_interface.py        # Should FAIL
legacy_code_handler.py     # Should FAIL
experimental_feature.py    # Should FAIL
```

**Expected Results**:
- All compound descriptive terms should be detected and flagged

### Test Case 3: Edge Cases and False Positives
**Objective**: Avoid false positives for legitimate technical terms

**Setup**:
```python
# These should PASS (legitimate technical terms)
user_model.py              # "user" is a domain term, not adjective
network_handler.py         # "network" is a domain term
database_connection.py     # "database" is a domain term
file_validator.py          # "file" is a domain term
api_client.py              # "api" is a domain term

# These should FAIL (descriptive adjectives)
final_version.py           # "final" is descriptive
working_solution.py        # "working" is descriptive
corrected_algorithm.py     # "corrected" is descriptive
```

**Expected Results**:
- Domain-specific terms should not trigger violations
- Descriptive adjectives should still be flagged

### Test Case 4: File Extension Handling
**Objective**: Ensure proper handling across different file types

**Setup**:
```python
# Test various file extensions
refactored_parser.py       # Python file
new_config.json           # JSON file
old_styles.css            # CSS file
backup_script.sh          # Shell script
temp_data.csv             # CSV file
```

**Expected Results**:
- All file types should be analyzed consistently
- Extensions should not affect adjective detection

### Test Case 5: Performance with Large Codebases
**Objective**: Ensure efficient processing of large directory structures

**Setup**:
- Create directory structure with 1000+ files
- Mix of valid and invalid naming patterns
- Measure processing time and memory usage

**Expected Results**:
- Processing time < 15 seconds for typical codebase
- Memory usage < 200MB
- Progress reporting for long operations

## Implementation Code

### Core Naming Convention Validator

```python
#!/usr/bin/env python3
"""
File Naming Convention Validator

Validates file naming conventions to detect adjective-based
names that indicate replacement files or technical debt.
"""

import re
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NamingViolation:
    """Represents a naming convention violation."""
    file_path: str
    file_name: str
    detected_adjectives: List[str]
    violation_type: str
    severity: str
    suggested_name: str
    line_number: int = 0  # Files don't have line numbers, but keeping for compatibility

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
            # Basic replacement indicators
            'refactored', 'new', 'old', 'backup', 'temp', 'temporary',
            'original', 'copy', 'duplicate', 'alternative', 'alternate',
            
            # Improvement indicators
            'improved', 'enhanced', 'optimized', 'better', 'updated',
            'revised', 'modified', 'changed', 'fixed', 'corrected',
            
            # State indicators
            'working', 'final', 'complete', 'incomplete', 'draft',
            'experimental', 'testing', 'debug', 'development', 'prod',
            'production', 'staging', 'beta', 'alpha', 'stable',
            
            # Quality indicators
            'good', 'bad', 'better', 'best', 'worst', 'fast', 'slow',
            'quick', 'slow', 'efficient', 'inefficient', 'clean', 'dirty',
            
            # Temporal indicators
            'recent', 'latest', 'current', 'previous', 'next', 'future',
            'past', 'ancient', 'modern', 'legacy', 'obsolete',
            
            # Version indicators
            'v1', 'v2', 'v3', 'version1', 'version2', 'version3',
            '1.0', '2.0', '3.0', 'final', 'release', 'candidate',
            
            # Status indicators
            'active', 'inactive', 'enabled', 'disabled', 'on', 'off',
            'true', 'false', 'yes', 'no', 'positive', 'negative',
            
            # Descriptive terms
            'simple', 'complex', 'basic', 'advanced', 'standard',
            'custom', 'special', 'generic', 'specific', 'general',
            
            # Action indicators (when used as adjectives)
            'running', 'stopped', 'starting', 'ending', 'processing',
            'loading', 'saving', 'creating', 'deleting', 'updating'
        }
        
        # Domain-specific terms that should NOT be flagged
        self.domain_terms = {
            # Technical domain terms
            'user', 'admin', 'system', 'network', 'database', 'api',
            'http', 'https', 'ftp', 'ssh', 'tcp', 'udp', 'ip',
            'file', 'folder', 'directory', 'path', 'url', 'uri',
            
            # Business domain terms
            'customer', 'product', 'order', 'invoice', 'payment',
            'account', 'profile', 'session', 'token', 'auth',
            
            # Application-specific terms
            'main', 'app', 'core', 'base', 'common', 'shared',
            'util', 'helper', 'manager', 'service', 'client',
            
            # Data terms
            'model', 'view', 'controller', 'entity', 'record',
            'data', 'info', 'config', 'setting', 'option'
        }
        
        # Compile regex patterns for efficient matching
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for detecting adjectives in filenames
        # Matches word boundaries to avoid partial matches
        adjective_pattern = r'\b(' + '|'.join(re.escape(word) for word in self.replacement_adjectives) + r')\b'
        self.adjective_regex = re.compile(adjective_pattern, re.IGNORECASE)
        
        # Pattern for compound words (e.g., "new_model", "old_handler")
        compound_pattern = r'\b(' + '|'.join(re.escape(word) for word in self.replacement_adjectives) + r')_[a-zA-Z0-9_]+'
        self.compound_regex = re.compile(compound_pattern, re.IGNORECASE)
        
        # Pattern for version numbers (v1, v2, 1.0, 2.0, etc.)
        version_pattern = r'\b(v\d+|version\d+|\d+\.\d+)\b'
        self.version_regex = re.compile(version_pattern, re.IGNORECASE)
    
    def detect_adjectives(self, filename: str) -> List[str]:
        """
        Detect descriptive adjectives in a filename.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            List of detected adjectives
        """
        detected = []
        base_name = Path(filename).stem  # Remove extension
        
        # Check for simple adjective matches
        simple_matches = self.adjective_regex.findall(base_name)
        detected.extend(simple_matches)
        
        # Check for compound word matches
        compound_matches = self.compound_regex.findall(base_name)
        detected.extend(compound_matches)
        
        # Check for version indicators
        version_matches = self.version_regex.findall(base_name)
        detected.extend(version_matches)
        
        # Remove duplicates and return
        return list(set(detected))
    
    def is_domain_term(self, word: str) -> bool:
        """
        Check if a word is a legitimate domain term.
        
        Args:
            word: Word to check
            
        Returns:
            True if it's a domain term, False otherwise
        """
        return word.lower() in self.domain_terms
    
    def suggest_improved_name(self, filename: str, detected_adjectives: List[str]) -> str:
        """
        Suggest an improved filename without descriptive adjectives.
        
        Args:
            filename: Original filename
            detected_adjectives: List of detected adjectives
            
        Returns:
            Suggested improved filename
        """
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        # Remove detected adjectives from the filename
        improved_name = base_name
        for adjective in detected_adjectives:
            # Remove adjective and following underscore/separator
            pattern = rf'\b{re.escape(adjective)}_?'
            improved_name = re.sub(pattern, '', improved_name, flags=re.IGNORECASE)
        
        # Clean up any double underscores or trailing separators
        improved_name = re.sub(r'_+', '_', improved_name).strip('_')
        
        # If the name becomes empty or too short, suggest a generic name
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
        """
        Validate a single filename for naming convention compliance.
        
        Args:
            file_path: Path to the file
            
        Returns:
            NamingViolation if violation found, None otherwise
        """
        filename = file_path.name
        detected_adjectives = self.detector.detect_adjectives(filename)
        
        if not detected_adjectives:
            return None  # No violation
        
        # Filter out domain terms to avoid false positives
        filtered_adjectives = [
            adj for adj in detected_adjectives 
            if not self.detector.is_domain_term(adj)
        ]
        
        if not filtered_adjectives:
            return None  # Only domain terms detected
        
        # Determine severity based on number and type of adjectives
        severity = self._determine_severity(filtered_adjectives)
        
        # Generate suggested name
        suggested_name = self.detector.suggest_improved_name(filename, filtered_adjectives)
        
        return NamingViolation(
            file_path=str(file_path),
            file_name=filename,
            detected_adjectives=filtered_adjectives,
            violation_type="descriptive_adjective",
            severity=severity,
            suggested_name=suggested_name,
            line_number=0
        )
    
    def _determine_severity(self, adjectives: List[str]) -> str:
        """
        Determine violation severity based on detected adjectives.
        
        Args:
            adjectives: List of detected adjectives
            
        Returns:
            Severity level (critical, major, minor)
        """
        critical_adjectives = {'backup', 'temp', 'temporary', 'old', 'obsolete'}
        major_adjectives = {'refactored', 'new', 'improved', 'enhanced', 'optimized'}
        
        if any(adj in critical_adjectives for adj in adjectives):
            return 'critical'
        elif any(adj in major_adjectives for adj in adjectives):
            return 'major'
        else:
            return 'minor'
    
    def scan_directory(self, root_path: Path) -> NamingValidationResult:
        """
        Recursively scan directory for naming convention violations.
        
        Args:
            root_path: Root directory to scan
            
        Returns:
            NamingValidationResult with analysis results
        """
        # Get all files (excluding directories)
        all_files = [f for f in root_path.rglob('*') if f.is_file()]
        logger.info(f"Found {len(all_files)} files to validate")
        
        violations = []
        valid_count = 0
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.validate_filename, file_path): file_path 
                for file_path in all_files
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result is None:
                        valid_count += 1
                    else:
                        violations.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Failed to validate {file_path}: {e}")
        
        total_files = len(all_files)
        compliance_rate = (valid_count / total_files * 100) if total_files > 0 else 100
        
        return NamingValidationResult(
            total_files=total_files,
            valid_files=valid_count,
            violated_files=len(violations),
            violations=violations,
            compliance_rate=compliance_rate,
            timestamp=__import__('datetime').datetime.now().isoformat()
        )
    
    def generate_report(self, result: NamingValidationResult) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Args:
            result: NamingValidationResult object
            
        Returns:
            Dictionary containing the validation report
        """
        # Group violations by severity
        violations_by_severity = {
            'critical': [v for v in result.violations if v.severity == 'critical'],
            'major': [v for v in result.violations if v.severity == 'major'],
            'minor': [v for v in result.violations if v.severity == 'minor']
        }
        
        # Count most common adjectives
        adjective_counts = {}
        for violation in result.violations:
            for adjective in violation.detected_adjectives:
                adjective_counts[adjective] = adjective_counts.get(adjective, 0) + 1
        
        report = {
            'summary': {
                'total_files_analyzed': result.total_files,
                'valid_files': result.valid_files,
                'violated_files': result.violated_files,
                'compliance_rate': result.compliance_rate,
                'analysis_timestamp': result.timestamp
            },
            'violations_by_severity': {
                severity: [
                    {
                        'file_path': v.file_path,
                        'file_name': v.file_name,
                        'detected_adjectives': v.detected_adjectives,
                        'suggested_name': v.suggested_name
                    }
                    for v in violations
                ]
                for severity, violations in violations_by_severity.items()
            },
            'adjective_frequency': dict(sorted(adjective_counts.items(), 
                                             key=lambda x: x[1], reverse=True)),
            'recommendations': self._generate_recommendations(result)
        }
        
        return report
    
    def _generate_recommendations(self, result: NamingValidationResult) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if result.violated_files == 0:
            recommendations.append("All files follow naming conventions. Great job!")
        else:
            recommendations.append(f"Found {result.violated_files} files with descriptive adjectives.")
            
            if result.compliance_rate < 80:
                recommendations.append("Compliance rate is below 80%. Consider systematic renaming.")
            elif result.compliance_rate < 95:
                recommendations.append("Compliance rate could be improved. Review flagged files.")
            
            # Suggest most common fixes
            if result.violations:
                recommendations.append("Focus on removing the most common descriptive adjectives first.")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save validation report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to {output_path}")

def main():
    """Main entry point for the naming convention validator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate file naming conventions and detect descriptive adjectives'
    )
    parser.add_argument(
        'path', 
        help='Directory or file path to validate'
    )
    parser.add_argument(
        '--output', 
        type=str,
        default='naming_convention_report.json',
        help='Output report file path'
    )
    parser.add_argument(
        '--workers', 
        type=int,
        default=4,
        help='Number of worker threads (default: 4)'
    )
    parser.add_argument(
        '--min-compliance', 
        type=float,
        default=95.0,
        help='Minimum compliance percentage (default: 95.0)'
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = NamingConventionValidator(max_workers=args.workers)
    
    # Validate target path
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"Path does not exist: {target_path}")
        sys.exit(1)
    
    logger.info(f"Starting naming convention validation of {target_path}")
    
    if target_path.is_file():
        # Single file validation
        violation = validator.validate_filename(target_path)
        if violation:
            print(f"VIOLATION: {violation.file_name}")
            print(f"  Detected adjectives: {violation.detected_adjectives}")
            print(f"  Suggested name: {violation.suggested_name}")
            result = NamingValidationResult(
                total_files=1,
                valid_files=0,
                violated_files=1,
                violations=[violation],
                compliance_rate=0.0,
                timestamp=__import__('datetime').datetime.now().isoformat()
            )
        else:
            print("VALID: No naming convention violations found")
            result = NamingValidationResult(
                total_files=1,
                valid_files=1,
                violated_files=0,
                violations=[],
                compliance_rate=100.0,
                timestamp=__import__('datetime').datetime.now().isoformat()
            )
    else:
        # Directory validation
        result = validator.scan_directory(target_path)
    
    # Generate and save report
    report = validator.generate_report(result)
    validator.save_report(report, Path(args.output))
    
    # Print summary
    print(f"\n=== Naming Convention Validation Summary ===")
    print(f"Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Valid files: {report['summary']['valid_files']}")
    print(f"Violated files: {report['summary']['violated_files']}")
    print(f"Compliance rate: {report['summary']['compliance_rate']:.2f}%")
    
    if report['violations_by_severity']['critical']:
        print(f"\nCritical violations: {len(report['violations_by_severity']['critical'])}")
        for violation in report['violations_by_severity']['critical'][:5]:  # Show first 5
            print(f"  - {violation['file_name']}: {violation['detected_adjectives']}")
    
    # Check compliance threshold
    compliance_ok = report['summary']['compliance_rate'] >= args.min_compliance
    if not compliance_ok:
        print(f"\nWARNING: Compliance rate {report['summary']['compliance_rate']:.2f}% "
              f"is below minimum threshold {args.min_compliance}%")
    
    return 0 if compliance_ok else 1

if __name__ == '__main__':
    sys.exit(main())
```

## Success Criteria

### Functional Requirements
- [ ] Accurately detect descriptive adjectives in filenames
- [ ] Avoid false positives for legitimate domain terms
- [ ] Handle compound words and variations
- [ ] Support all common file extensions
- [ ] Generate meaningful suggested names
- [ ] Provide severity-based violation classification

### Performance Requirements
- [ ] Process typical codebase (< 1000 files) in under 15 seconds
- [ ] Memory usage stays below 200MB during validation
- [ ] Provide progress feedback for long-running operations
- [ ] Support parallel processing for efficiency

### Quality Requirements
- [ ] 95%+ accuracy in adjective detection
- [ ] Zero false positives for domain-specific terms
- [ ] Proper handling of edge cases (empty files, special characters)
- [ ] Cross-platform compatibility

### Integration Requirements
- [ ] Generate NamingConvention entities compatible with data model
- [ ] Integrate with QualityGate system for automated enforcement
- [ ] Support CI/CD pipeline integration via exit codes
- [ ] Provide JSON output for programmatic consumption

## Integration

### CI/CD Pipeline Integration

```yaml
# .github/workflows/naming-convention-check.yml
name: Naming Convention Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate-naming:
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
    
    - name: Run Naming Convention Validation
      run: |
        python tools/naming_validator.py src/ --output reports/naming_report.json --min-compliance 95.0
    
    - name: Upload Report
      uses: actions/upload-artifact@v3
      with:
        name: naming-convention-report
        path: reports/naming_report.json
    
    - name: Check Compliance
      run: |
        python -c "
        import json
        with open('reports/naming_report.json') as f:
            report = json.load(f)
        compliance = report['summary']['compliance_rate']
        if compliance < 95.0:
            print(f'Compliance rate {compliance:.2f}% is below 95% threshold!')
            exit(1)
        print(f'Compliance rate {compliance:.2f}% meets threshold.')
        "
```

### Quality Gate Integration

```python
# Integration with QualityGate system
class NamingConventionQualityGate:
    """Quality gate for naming convention validation."""
    
    def __init__(self, min_compliance: float = 95.0):
        self.min_compliance = min_compliance
        self.gate_id = "naming-convention"
    
    def evaluate(self, validation_result: NamingValidationResult) -> QualityGateResult:
        """Evaluate if the codebase passes the naming convention gate."""
        return QualityGateResult(
            gate_id=self.gate_id,
            passed=validation_result.compliance_rate >= self.min_compliance,
            violations=validation_result.violations,
            compliance_rate=validation_result.compliance_rate
        )
```

### Automated Refactoring Suggestions

```python
def generate_refactoring_script(violations: List[NamingViolation]) -> str:
    """Generate a bash script to automatically rename files."""
    script_lines = ["#!/bin/bash", "echo 'Renaming files with descriptive adjectives...'"]
    
    for violation in violations:
        old_name = violation.file_path
        new_name = old_name.replace(violation.file_name, violation.suggested_name)
        script_lines.append(f"mv '{old_name}' '{new_name}'")
    
    script_lines.append("echo 'Renaming complete.'")
    return "\n".join(script_lines)
```

---

**Test Plan Status**: ✅ Complete  
**Ready for Implementation**: ✅ Yes  
**Next Phase**: Implementation and Integration Testing