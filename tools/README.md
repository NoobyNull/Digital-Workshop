# Phase 0: Dependency Analysis and Migration Planning Tools

This directory contains the complete set of tools for Phase 0 of the GUI Layout Refactoring project. These tools provide comprehensive dependency mapping, automated detection of hardcoded styles, backward compatibility layers, migration utilities, and visual regression testing.

## Overview

Phase 0 establishes the foundation for safe migration from the legacy theme system to qt-material by:

1. **Creating comprehensive dependency mapping** for all theme-related components
2. **Building automated tools** to identify all hardcoded styles
3. **Implementing backward compatibility layers** for ThemeManager
4. **Creating migration utilities** for systematic updates
5. **Setting up testing frameworks** to verify changes

## Tools

### 1. Dependency Analysis Tool (`dependency_analysis.py`)

Comprehensive analyzer for theme-related dependencies across the entire codebase.

**Features:**
- Maps all ThemeManager usage patterns
- Identifies setStyleSheet() calls with hardcoded styles
- Assesses migration risk levels (high, medium, low)
- Generates detailed migration plans with priority ordering
- Supports multiple output formats (JSON, HTML, Markdown)

**Usage:**
```bash
# Analyze entire codebase
python tools/dependency_analysis.py

# Generate HTML report
python tools/dependency_analysis.py --format html --output dependency_report.html

# Include test files in analysis
python tools/dependency_analysis.py --include-tests

# Analyze specific directory
python tools/dependency_analysis.py --root-path src/gui
```

**Output:**
- **JSON Report:** Complete analysis data with migration recommendations
- **HTML Report:** Visual dashboard with risk distribution and file details
- **Markdown Report:** Human-readable summary with migration priorities

### 2. StyleSheet Detection Tool (`stylesheet_detector.py`)

Advanced detector for hardcoded styles in setStyleSheet() calls with detailed analysis.

**Features:**
- Identifies all setStyleSheet() calls with context
- Analyzes hardcoded colors and Qt properties
- Assesses migration complexity and risk
- Provides specific migration suggestions
- Tracks common color patterns across the codebase

**Usage:**
```bash
# Detect all hardcoded styles
python tools/stylesheet_detector.py

# Only show high-risk files
python tools/stylesheet_detector.py --min-risk high

# Generate detailed HTML report
python tools/stylesheet_detector.py --format html --output stylesheet_report.html

# Focus on specific components
python tools/stylesheet_detector.py --files src/gui/main_window.py src/gui/preferences.py
```

**Risk Assessment:**
- **High Risk:** Multiple hardcoded colors, complex nested styles
- **Medium Risk:** Single hardcoded colors, inline style properties
- **Low Risk:** Already using variables or qt-material integration

### 3. Migration Utilities (`migration_utils.py`)

Automated code migration tool for updating imports and converting styles.

**Features:**
- Updates import statements to use UnifiedThemeManager
- Converts hardcoded styles to qt-material variables
- Creates backup files before making changes
- Validates migration completeness
- Generates comprehensive migration reports

**Usage:**
```bash
# Update import statements (dry run)
python tools/migration_utils.py update-imports --dry-run

# Migrate styles with backups
python tools/migration_utils.py migrate-styles --backup

# Validate migration completeness
python tools/migration_utils.py validate-migration

# Generate complete migration report
python tools/migration_utils.py generate-report --output migration_report.json
```

**Migration Commands:**
- `update-imports`: Convert legacy ThemeManager imports to UnifiedThemeManager
- `migrate-styles`: Convert hardcoded styles to qt-material variables
- `validate-migration`: Check migration completeness and identify remaining issues
- `generate-report`: Create comprehensive migration progress report

### 4. Visual Regression Testing Framework (`visual_regression_tester.py`)

Comprehensive visual testing framework to ensure UI consistency during migration.

**Features:**
- Captures screenshots of UI components before and after changes
- Compares images pixel-by-pixel with configurable thresholds
- Generates detailed HTML reports with side-by-side comparisons
- Supports baseline generation and automated testing
- Tracks visual differences and highlights problem areas

**Usage:**
```bash
# Generate baseline images for all components
python tools/visual_regression_tester.py --generate-baselines

# Run visual regression tests
python tools/visual_regression_tester.py

# Test specific components with custom threshold
python tools/visual_regression_tester.py --components main_window dialog --threshold 0.02

# Generate detailed HTML report
python tools/visual_regression_tester.py --output visual_report.html
```

**Test Results:**
- **Pixel Difference:** Percentage of pixels that differ between baseline and current
- **Max Difference:** Maximum color difference found (0-1 scale)
- **Visual Comparison:** Side-by-side images with highlighted differences
- **Pass/Fail Status:** Based on configurable pixel difference threshold

## Migration Workflow

### Step 1: Analysis Phase
```bash
# 1. Analyze dependencies and create migration plan
python tools/dependency_analysis.py --format html --output analysis_report.html

# 2. Detect hardcoded styles and assess risks
python tools/stylesheet_detector.py --format html --output styles_report.html

# 3. Generate comprehensive migration report
python tools/migration_utils.py generate-report --output migration_plan.json
```

### Step 2: Planning Phase
1. **Review Analysis Reports:**
   - Identify high-risk files requiring immediate attention
   - Plan migration phases based on risk levels and dependencies
   - Schedule testing and validation checkpoints

2. **Set Up Testing:**
   ```bash
   # Generate baseline images for visual regression testing
   python tools/visual_regression_tester.py --generate-baselines
   ```

### Step 3: Migration Phase
```bash
# 1. Update import statements (start with low-risk files)
python tools/migration_utils.py update-imports --files src/gui/components/*.py --dry-run
python tools/migration_utils.py update-imports --files src/gui/components/*.py

# 2. Migrate hardcoded styles (medium-risk files)
python tools/migration_utils.py migrate-styles --files src/gui/preferences.py --backup

# 3. Validate progress
python tools/migration_utils.py validate-migration
```

### Step 4: Testing Phase
```bash
# 1. Run visual regression tests
python tools/visual_regression_tester.py --components main_window preferences

# 2. Test application functionality
python -m pytest tests/test_theme_*.py -v

# 3. Manual testing and visual inspection
# Run the application and verify theme switching works correctly
```

### Step 5: Validation Phase
```bash
# 1. Generate final migration report
python tools/migration_utils.py generate-report --output final_report.json

# 2. Run comprehensive visual regression tests
python tools/visual_regression_tester.py

# 3. Validate no legacy dependencies remain
python tools/dependency_analysis.py --include-tests
```

## Backward Compatibility

The tools maintain full backward compatibility through:

1. **LegacyThemeManager Class:** Enhanced compatibility layer that delegates to UnifiedThemeManager
2. **Import Aliases:** Maintains existing import patterns during transition
3. **Gradual Migration:** Allows incremental updates without breaking existing code
4. **Migration Warnings:** Provides guidance when legacy methods are used

## Configuration

### Risk Thresholds
- **High Risk:** Files with ThemeManager.instance() calls or complex hardcoded styles
- **Medium Risk:** Files with hardcoded colors or inline style properties
- **Low Risk:** Files already using variables or qt-material integration

### Migration Priorities
1. **Priority 1-3:** High-risk files requiring immediate migration
2. **Priority 4-7:** Medium-risk files for phased migration
3. **Priority 8-10:** Low-risk files for final cleanup

### Visual Testing Thresholds
- **Default Threshold:** 0.05 (5% pixel difference allowed)
- **Strict Threshold:** 0.01 (1% for critical UI components)
- **Relaxed Threshold:** 0.10 (10% for non-critical components)

## Troubleshooting

### Common Issues

1. **Import Errors After Migration:**
   ```bash
   # Check for remaining legacy imports
   python tools/migration_utils.py validate-migration
   ```

2. **Visual Regression Test Failures:**
   ```bash
   # Regenerate baselines if intentional changes were made
   python tools/visual_regression_tester.py --generate-baselines --components failed_component
   ```

3. **Migration Tool Crashes:**
   ```bash
   # Run with verbose logging to identify issues
   python tools/migration_utils.py update-imports --verbose --dry-run
   ```

### Recovery Procedures

1. **Restore from Backups:**
   ```bash
   # Migration utilities create .migration_backup files
   # Restore manually if needed
   cp file.py.migration_backup file.py
   ```

2. **Reset to Baseline:**
   ```bash
   # Regenerate all baselines if major changes occurred
   python tools/visual_regression_tester.py --generate-baselines
   ```

## Integration with CI/CD

### Automated Testing Pipeline
```bash
#!/bin/bash
# Example CI/CD integration script

# Run dependency analysis
python tools/dependency_analysis.py --format json --output ci_dependency_report.json

# Run style detection
python tools/stylesheet_detector.py --format json --output ci_styles_report.json

# Run visual regression tests
python tools/visual_regression_tester.py --threshold 0.02 --output ci_visual_report.html

# Validate migration completeness
python tools/migration_utils.py validate-migration

# Check if migration completeness meets requirements
COMPLETENESS=$(python -c "
import json
with open('migration_plan.json') as f:
    data = json.load(f)
    print(data['summary']['migration_completeness'])
")

if (( $(echo "$COMPLETENESS < 95" | bc -l) )); then
    echo "Migration completeness below 95%: $COMPLETENESS%"
    exit 1
fi
```

### Pre-commit Hooks
```bash
#!/bin/bash
# Example pre-commit hook

# Check for new hardcoded styles
python tools/stylesheet_detector.py --min-risk medium --format json | jq '.summary.total_files_analyzed'

# Validate import consistency
python tools/migration_utils.py validate-migration
```

## Performance Considerations

### Tool Performance
- **Dependency Analysis:** ~30 seconds for full codebase scan
- **Style Detection:** ~15 seconds for targeted analysis
- **Visual Testing:** ~2-5 seconds per component
- **Migration:** ~1 second per file (with backups)

### Memory Usage
- **Analysis Tools:** ~50-100MB RAM during execution
- **Visual Testing:** ~200-500MB RAM for image processing
- **Migration Tools:** ~20-50MB RAM with file caching

### Optimization Tips
1. **Use specific file lists** instead of scanning entire codebase
2. **Set appropriate risk thresholds** to focus on critical issues
3. **Run visual tests in parallel** for multiple components
4. **Use dry-run mode** for validation before making changes

## Contributing

When adding new tools or features:

1. **Follow existing patterns** for command-line interfaces
2. **Include comprehensive logging** with appropriate levels
3. **Add unit tests** for new functionality
4. **Update documentation** with usage examples
5. **Consider backward compatibility** for existing workflows

## Support

For issues or questions:

1. **Check the troubleshooting section** for common solutions
2. **Run tools with verbose logging** (`--verbose` flag)
3. **Generate comprehensive reports** for debugging
4. **Review migration patterns** in existing codebase

## License

These tools are part of the GUI Layout Refactoring project and follow the same licensing terms as the main application.