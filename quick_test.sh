#!/bin/bash
# Quick Test Runner Script for Candy-Cadence
# Runs all tests with various options

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Main menu
show_menu() {
    print_header "Candy-Cadence Test Runner"
    echo ""
    echo "1) Run all tests (basic)"
    echo "2) Run all tests (verbose)"
    echo "3) Run all tests (stop on first failure)"
    echo "4) Run all tests (detailed with reports)"
    echo "5) Generate JSON report"
    echo "6) Generate HTML report"
    echo "7) Generate both reports"
    echo "8) Exit"
    echo ""
    read -p "Select option (1-8): " choice
}

# Run tests
run_basic() {
    print_header "Running Basic Tests"
    python run_all_tests.py
}

run_verbose() {
    print_header "Running Tests (Verbose)"
    python run_all_tests.py --verbose
}

run_failfast() {
    print_header "Running Tests (Fail Fast)"
    python run_all_tests.py --failfast
}

run_detailed() {
    print_header "Running Detailed Tests"
    python run_all_tests_detailed.py
}

run_json_report() {
    print_header "Generating JSON Report"
    REPORT_FILE="test_report_$(date +%Y%m%d_%H%M%S).json"
    python run_all_tests_detailed.py --json "$REPORT_FILE"
    print_success "Report saved to: $REPORT_FILE"
}

run_html_report() {
    print_header "Generating HTML Report"
    REPORT_FILE="test_report_$(date +%Y%m%d_%H%M%S).html"
    python run_all_tests_detailed.py --html "$REPORT_FILE"
    print_success "Report saved to: $REPORT_FILE"
    if command -v xdg-open &> /dev/null; then
        xdg-open "$REPORT_FILE"
    elif command -v open &> /dev/null; then
        open "$REPORT_FILE"
    fi
}

run_both_reports() {
    print_header "Generating Both Reports"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    JSON_FILE="test_report_${TIMESTAMP}.json"
    HTML_FILE="test_report_${TIMESTAMP}.html"
    python run_all_tests_detailed.py --json "$JSON_FILE" --html "$HTML_FILE"
    print_success "JSON report saved to: $JSON_FILE"
    print_success "HTML report saved to: $HTML_FILE"
}

# Main loop
while true; do
    show_menu
    case $choice in
        1) run_basic ;;
        2) run_verbose ;;
        3) run_failfast ;;
        4) run_detailed ;;
        5) run_json_report ;;
        6) run_html_report ;;
        7) run_both_reports ;;
        8) print_info "Exiting..."; exit 0 ;;
        *) print_error "Invalid option" ;;
    esac
    echo ""
    read -p "Press Enter to continue..."
done

