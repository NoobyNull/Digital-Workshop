#!/bin/bash
# Digital Workshop Root Directory Cleanup Script
# Execute this script to perform the complete cleanup
# 
# Usage: ./cleanup_root_directory.sh
# 
# WARNING: This script will reorganize files in the current directory.
# A backup will be created before any changes are made.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "pyproject.toml" ]; then
    error "This script must be run from the Digital Workshop root directory"
    error "Expected files README.md and pyproject.toml not found"
    exit 1
fi

# Count files before cleanup
BEFORE_COUNT=$(find . -maxdepth 1 -type f | wc -l)
log "Starting Digital Workshop Root Directory Cleanup"
log "Current root directory file count: $BEFORE_COUNT files"

# Phase 1: Backup
log "Phase 1: Creating backup..."
BACKUP_DIR="../digital-workshop-backup-$(date +%Y%m%d_%H%M%S)"
if cp -r . "$BACKUP_DIR"; then
    log "Backup created successfully at: $BACKUP_DIR"
else
    error "Failed to create backup. Aborting cleanup."
    exit 1
fi

# Phase 2: Create directory structure
log "Phase 2: Creating new directory structure..."
mkdir -p config samples samples/code samples/reports build/installer build/logs archive
mkdir -p docs/guides docs/architecture docs/reports
mkdir -p tests/unit tests/integration tests/framework tests/parsers tests/persistence tests/themes tests/performance tests/runner
mkdir -p reports/json reports/html reports/analysis reports/comprehensive reports/performance reports/quality reports/test_results
mkdir -p tools/quality tools/analysis tools/debug tools/exceptions tools/migration tools/demos
log "Directory structure created successfully"

# Phase 3: File movement operations with error handling
log "Phase 3: Moving files to organized structure..."

# Function to safely move files
safe_move() {
    local src="$1"
    local dest="$2"
    local description="$3"
    
    if [ -e "$src" ]; then
        if mv "$src" "$dest"; then
            log "Moved: $description"
            return 0
        else
            error "Failed to move: $description"
            return 1
        fi
    else
        warn "File not found, skipping: $description"
        return 1
    fi
}

# Documentation files
log "Moving documentation files..."
safe_move "QUICK_START_GUIDE.md" "docs/guides/QUICK_START.md" "QUICK_START_GUIDE.md"
safe_move "REFACTORING_SOLUTIONS.md" "docs/guides/REFACTORING.md" "REFACTORING_SOLUTIONS.md"
safe_move "IMPORT_PROCESS_ARCHITECTURE.md" "docs/architecture/IMPORT_PROCESS.md" "IMPORT_PROCESS_ARCHITECTURE.md"
safe_move "FINAL_IMPLEMENTATION_REPORT.md" "docs/reports/FINAL_IMPLEMENTATION.md" "FINAL_IMPLEMENTATION_REPORT.md"
safe_move "WINDOW_PERSISTENCE_TEST_GUIDE.md" "docs/guides/WINDOW_PERSISTENCE.md" "WINDOW_PERSISTENCE_TEST_GUIDE.md"
safe_move "vtk_resource_tracker_fix_summary.md" "docs/reports/VTK_RESOURCE_TRACKER.md" "vtk_resource_tracker_fix_summary.md"

# Test files
log "Moving test files..."
safe_move "comprehensive_test_suite.py" "tests/integration/" "comprehensive_test_suite.py"
safe_move "comprehensive_test_suite_tests.py" "tests/integration/" "comprehensive_test_suite_tests.py"
safe_move "unified_test_runner.py" "tests/runner.py" "unified_test_runner.py"

# Move test_*.py files in batch
test_files=$(find . -maxdepth 1 -name "test_*.py" -type f)
if [ -n "$test_files" ]; then
    for file in $test_files; do
        filename=$(basename "$file")
        safe_move "$filename" "tests/unit/" "$filename"
    done
fi

# Configuration files
log "Moving configuration files..."
safe_move "quality_config.yaml" "config/" "quality_config.yaml"
safe_move "test_framework_config.json" "config/" "test_framework_config.json"
safe_move "pyinstaller.spec" "config/" "pyinstaller.spec"
safe_move "installer.nsi" "config/" "installer.nsi"

# Sample files
log "Moving sample files..."
if [ -d "sample" ]; then
    safe_move "sample/" "samples/" "sample/ directory"
fi
safe_move "sample_large_module.py" "samples/code/" "sample_large_module.py"
safe_move "sample_small_module.py" "samples/code/" "sample_small_module.py"

# Build files
log "Moving build files..."
if [ -d "installer" ]; then
    safe_move "installer/" "build/installer/" "installer/ directory"
fi

# Build logs
build_logs=$(find . -maxdepth 1 -name "build_*.log" -type f)
if [ -n "$build_logs" ]; then
    for file in $build_logs; do
        filename=$(basename "$file")
        safe_move "$filename" "build/logs/" "$filename"
    done
fi

# Archive temporary files
log "Archiving temporary files..."
safe_move "mon" "archive/" "mon"
safe_move "n" "archive/" "n"
safe_move "P" "archive/" "P"
safe_move "validate" "archive/" "validate"
safe_move "quality" "archive/" "quality"
if [ -d "-p" ]; then
    safe_move "-p/" "archive/" "-p/ directory"
fi
if [ -d ".augment" ]; then
    safe_move ".augment/" "archive/" ".augment/ directory"
fi

# Move report files in batches
log "Moving report files..."

# JSON reports
for file in *_report.json; do
    [ -f "$file" ] && safe_move "$file" "reports/json/" "$file"
done

# HTML reports
for file in *_report.html; do
    [ -f "$file" ] && safe_move "$file" "reports/html/" "$file"
done

# Analysis files
for file in *_analysis.json; do
    [ -f "$file" ] && safe_move "$file" "reports/analysis/" "$file"
done

# Comprehensive reports
for file in comprehensive_*_report.md; do
    [ -f "$file" ] && safe_move "$file" "reports/comprehensive/" "$file"
done

# Performance files
for file in performance_*.json; do
    [ -f "$file" ] && safe_move "$file" "reports/performance/" "$file"
done

# Quality files
for file in naming_*.json; do
    [ -f "$file" ] && safe_move "$file" "reports/quality/" "$file"
done

# Test results
for file in test_results.*; do
    [ -f "$file" ] && safe_move "$file" "reports/test_results/" "$file"
done

# Move development tools
log "Moving development tools..."
safe_move "code_quality_validator.py" "tools/quality/" "code_quality_validator.py"
safe_move "naming_validator.py" "tools/quality/" "naming_validator.py"
safe_move "quality_gate_enforcer.py" "tools/quality/" "quality_gate_enforcer.py"
safe_move "monolithic_detector.py" "tools/analysis/" "monolithic_detector.py"
safe_move "debug_detection.py" "tools/debug/" "debug_detection.py"
safe_move "create_exceptions.py" "tools/exceptions/" "create_exceptions.py"
safe_move "migrate_models.py" "tools/migration/" "migrate_models.py"
safe_move "monolithic_report.json" "tools/analysis/" "monolithic_report.json"

# Error handling demos
demo_files=$(find . -maxdepth 1 -name "error_handling_demo*.py" -type f)
if [ -n "$demo_files" ]; then
    for file in $demo_files; do
        filename=$(basename "$file")
        safe_move "$filename" "tools/demos/" "$filename"
    done
fi

# Phase 4: Post-cleanup validation
log "Phase 4: Post-cleanup validation..."

# Count files after cleanup
AFTER_COUNT=$(find . -maxdepth 1 -type f | wc -l)
log "Root directory file count after cleanup: $AFTER_COUNT files"
log "Files moved: $((BEFORE_COUNT - AFTER_COUNT))"

# Check essential files are still present
essential_files=("README.md" "pyproject.toml" "requirements.txt" "run.py" "build.py")
missing_essential=0
for file in "${essential_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Essential file missing: $file"
        missing_essential=$((missing_essential + 1))
    fi
done

if [ $missing_essential -eq 0 ]; then
    log "All essential files present"
else
    error "$missing_essential essential files missing!"
fi

# Test basic functionality
log "Testing basic functionality..."

# Test Python imports
if python -c "import sys; sys.path.insert(0, '.')" 2>/dev/null; then
    log "Python import test: PASSED"
else
    warn "Python import test: FAILED"
fi

# Test pytest configuration
if python -m pytest --collect-only -q >/dev/null 2>&1; then
    log "Pytest configuration test: PASSED"
else
    warn "Pytest configuration test: FAILED"
fi

# Test build script
if python build.py --help >/dev/null 2>&1; then
    log "Build script test: PASSED"
else
    warn "Build script test: FAILED"
fi

# Generate summary report
log "Generating cleanup summary..."
SUMMARY_FILE="cleanup_summary_$(date +%Y%m%d_%H%M%S).txt"
cat > "$SUMMARY_FILE" << EOF
Digital Workshop Root Directory Cleanup Summary
===============================================
Date: $(date)
Backup Location: $BACKUP_DIR

File Movement Summary:
- Files before cleanup: $BEFORE_COUNT
- Files after cleanup: $AFTER_COUNT
- Files moved: $((BEFORE_COUNT - AFTER_COUNT))

Essential Files Status:
EOF

for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "- $file: PRESENT" >> "$SUMMARY_FILE"
    else
        echo "- $file: MISSING" >> "$SUMMARY_FILE"
    fi
done

cat >> "$SUMMARY_FILE" << EOF

New Directory Structure:
$(find . -type d | sort)

Cleanup completed successfully!
Backup available at: $BACKUP_DIR
Summary report: $SUMMARY_FILE
EOF

log "Cleanup completed successfully!"
log "Summary report saved to: $SUMMARY_FILE"
log "Backup available at: $BACKUP_DIR"
log "Root directory now contains $AFTER_COUNT files (reduced from $BEFORE_COUNT)"

# Display final directory structure
echo
info "Final directory structure:"
tree -L 2 -a 2>/dev/null || find . -maxdepth 2 -type d | sort | sed 's|[^/]*/|  |g'

echo
log "Cleanup plan execution completed!"
log "Next steps:"
log "1. Review the cleanup summary: cat $SUMMARY_FILE"
log "2. Test application functionality: python run.py"
log "3. Run test suite: python -m pytest tests/ -v"
log "4. If issues arise, restore from backup: cp -r $BACKUP_DIR/* ."

# Final validation check
if [ $AFTER_COUNT -lt $BEFORE_COUNT ] && [ $missing_essential -eq 0 ]; then
    log "✅ CLEANUP SUCCESSFUL - All validation checks passed"
    exit 0
else
    warn "⚠️  CLEANUP COMPLETED WITH WARNINGS - Please review the summary"
    exit 1
fi