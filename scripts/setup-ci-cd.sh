#!/bin/bash

################################################################################
# CI/CD Setup Automation Script for Comprehensive Testing Framework
# 
# This script automates the setup of CI/CD pipeline integration for the
# Comprehensive Testing Framework across multiple platforms.
#
# Usage: ./setup-ci-cd.sh [OPTIONS]
#
# Options:
#   --platform PLATFORM    Target platform (github, gitlab, jenkins, azure)
#   --environment ENV      Environment (development, staging, production)
#   --python-version VER   Python version (3.8, 3.9, 3.10, 3.11, 3.12)
#   --install-deps         Install all dependencies
#   --configure-gates      Configure quality gates
#   --validate-setup       Validate the setup
#   --help                 Show this help message
#
# Examples:
#   ./setup-ci-cd.sh --platform github --environment production
#   ./setup-ci-cd.sh --install-deps --configure-gates
#   ./setup-ci-cd.sh --validate-setup
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PLATFORM=""
ENVIRONMENT="development"
PYTHON_VERSION="3.11"
INSTALL_DEPS=false
CONFIGURE_GATES=false
VALIDATE_SETUP=false
VERBOSE=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

# Help function
show_help() {
    cat << EOF
CI/CD Setup Automation Script for Comprehensive Testing Framework

Usage: $0 [OPTIONS]

Options:
    --platform PLATFORM    Target platform (github, gitlab, jenkins, azure)
    --environment ENV      Environment (development, staging, production)
    --python-version VER   Python version (3.8, 3.9, 3.10, 3.11, 3.12)
    --install-deps         Install all dependencies
    --configure-gates      Configure quality gates
    --validate-setup       Validate the setup
    --verbose              Enable verbose output
    --help                 Show this help message

Examples:
    $0 --platform github --environment production
    $0 --install-deps --configure-gates
    $0 --validate-setup --verbose

Platforms:
    github     - GitHub Actions workflow
    gitlab     - GitLab CI configuration
    jenkins    - Jenkins pipeline setup
    azure      - Azure DevOps configuration

Environments:
    development - Lenient quality gates for development
    staging     - Moderate quality gates for staging
    production  - Strict quality gates for production

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --platform)
                PLATFORM="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --install-deps)
                INSTALL_DEPS=true
                shift
                ;;
            --configure-gates)
                CONFIGURE_GATES=true
                shift
                ;;
            --validate-setup)
                VALIDATE_SETUP=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_debug "Detected Linux OS"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_debug "Detected macOS"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        log_debug "Detected Windows"
    else
        log_warning "Unknown OS: $OSTYPE"
        OS="unknown"
    fi
    
    # Check required commands
    local required_commands=("python3" "pip3" "git" "curl")
    local missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_info "Please install the missing commands and try again"
        return 1
    fi
    
    # Check Python version
    local python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Found Python version: $python_version"
    
    # Check available disk space (minimum 1GB)
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 1 ]]; then
        log_warning "Low disk space: ${available_space}GB available"
    fi
    
    log_success "System requirements check completed"
    return 0
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Upgrade pip
    log_debug "Upgrading pip..."
    python3 -m pip install --upgrade pip setuptools wheel
    
    # Install base requirements
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_debug "Installing base requirements..."
        python3 -m pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
    
    # Install testing requirements
    if [[ -f "$PROJECT_ROOT/requirements_testing.txt" ]]; then
        log_debug "Installing testing requirements..."
        python3 -m pip install -r "$PROJECT_ROOT/requirements_testing.txt"
    fi
    
    # Install CI/CD specific dependencies
    local ci_deps=(
        "pytest>=7.0.0"
        "pytest-cov>=4.0.0"
        "pytest-html>=3.1.0"
        "pytest-json-report>=1.5.0"
        "pytest-timeout>=2.1.0"
        "pytest-mock>=3.10.0"
        "psutil>=5.9.0"
        "black>=22.0.0"
        "pylint>=2.15.0"
        "mypy>=1.0.0"
        "bandit>=1.7.0"
        "safety>=2.3.0"
        "coverage>=7.0.0"
        "memory-profiler>=0.60.0"
        "allure-pytest>=2.13.0"
    )
    
    log_debug "Installing CI/CD dependencies..."
    for dep in "${ci_deps[@]}"; do
        log_debug "Installing $dep"
        python3 -m pip install "$dep"
    done
    
    # Install comprehensive test suite if available
    if [[ -f "$PROJECT_ROOT/comprehensive_test_suite.py" ]]; then
        log_debug "Installing comprehensive test suite..."
        python3 -m pip install -e "$PROJECT_ROOT"
    fi
    
    log_success "Python dependencies installation completed"
}

# Configure quality gates
configure_quality_gates() {
    log_info "Configuring quality gates for $ENVIRONMENT environment..."
    
    local config_file="$PROJECT_ROOT/test_framework_config.json"
    
    # Create backup if config exists
    if [[ -f "$config_file" ]]; then
        cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
        log_debug "Created backup of existing config file"
    fi
    
    # Generate environment-specific configuration
    case $ENVIRONMENT in
        development)
            cat > "$config_file" << EOF
{
    "target_path": ".",
    "output_dir": "reports",
    "tools": {
        "monolithic_detector": {
            "enabled": true,
            "threshold": 1000,
            "workers": 4,
            "timeout": 300,
            "exclude_dirs": ["__pycache__", ".git", "node_modules", ".venv", "venv"],
            "file_extensions": [".py"],
            "include_subdirectories": true
        },
        "naming_validator": {
            "enabled": true,
            "workers": 4,
            "min_compliance": 90.0,
            "timeout": 300,
            "check_case": true,
            "check_underscores": true,
            "exclude_patterns": ["test_", "Test", "conftest.py", "setup.py"]
        },
        "unified_test_runner": {
            "enabled": true,
            "parallel_suites": true,
            "max_workers": 4,
            "timeout": 1800,
            "test_patterns": ["test_*.py", "*_test.py"],
            "coverage_threshold": 75.0,
            "fail_fast": false
        },
        "code_quality_validator": {
            "enabled": true,
            "parallel_execution": true,
            "timeout": 600,
            "black_format": true,
            "pylint_check": true,
            "max_line_length": 88,
            "ignore_patterns": ["__pycache__/*", ".git/*"]
        },
        "quality_gate_enforcer": {
            "enabled": true,
            "parallel": true,
            "timeout": 300,
            "enforce_monolithic_gates": true,
            "enforce_naming_gates": true,
            "enforce_test_gates": true,
            "enforce_quality_gates": true
        }
    },
    "reporting": {
        "formats": ["json", "html", "console"],
        "include_charts": true,
        "include_recommendations": true,
        "include_performance_metrics": true,
        "output_detailed_reports": true,
        "export_summary_only": false
    },
    "performance": {
        "max_total_time": 1800,
        "memory_limit_mb": 4096,
        "parallel_execution": true,
        "max_concurrent_tools": 5,
        "progress_update_interval": 1.0,
        "enable_memory_monitoring": true,
        "enable_cpu_monitoring": true
    },
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 2,
            "severity": "major",
            "enforce": true,
            "description": "Maximum 2 monolithic modules allowed in development"
        },
        "naming_conventions": {
            "threshold": 90.0,
            "severity": "minor",
            "enforce": true,
            "description": "90% compliance with naming conventions"
        },
        "test_execution": {
            "threshold": 85.0,
            "severity": "major",
            "enforce": true,
            "description": "85% test pass rate"
        },
        "code_quality": {
            "threshold": 85.0,
            "severity": "minor",
            "enforce": true,
            "description": "85% code quality score"
        },
        "performance_score": {
            "threshold": 75.0,
            "severity": "minor",
            "enforce": false,
            "description": "75% performance score threshold"
        }
    },
    "logging": {
        "level": "INFO",
        "enable_file_logging": true,
        "log_file_path": "logs/test_framework.log",
        "max_log_size_mb": 10,
        "backup_count": 5,
        "enable_console_logging": true
    },
    "ci_cd": {
        "enabled": true,
        "fail_on_critical": true,
        "fail_on_major": true,
        "fail_on_minor": false,
        "environment": "development"
    }
}
EOF
            ;;
        staging)
            cat > "$config_file" << EOF
{
    "target_path": ".",
    "output_dir": "reports",
    "tools": {
        "monolithic_detector": {
            "enabled": true,
            "threshold": 750,
            "workers": 4,
            "timeout": 300,
            "exclude_dirs": ["__pycache__", ".git", "node_modules", ".venv", "venv"],
            "file_extensions": [".py"],
            "include_subdirectories": true
        },
        "naming_validator": {
            "enabled": true,
            "workers": 4,
            "min_compliance": 92.5,
            "timeout": 300,
            "check_case": true,
            "check_underscores": true,
            "exclude_patterns": ["test_", "Test", "conftest.py", "setup.py"]
        },
        "unified_test_runner": {
            "enabled": true,
            "parallel_suites": true,
            "max_workers": 4,
            "timeout": 1800,
            "test_patterns": ["test_*.py", "*_test.py"],
            "coverage_threshold": 80.0,
            "fail_fast": false
        },
        "code_quality_validator": {
            "enabled": true,
            "parallel_execution": true,
            "timeout": 600,
            "black_format": true,
            "pylint_check": true,
            "max_line_length": 88,
            "ignore_patterns": ["__pycache__/*", ".git/*"]
        },
        "quality_gate_enforcer": {
            "enabled": true,
            "parallel": true,
            "timeout": 300,
            "enforce_monolithic_gates": true,
            "enforce_naming_gates": true,
            "enforce_test_gates": true,
            "enforce_quality_gates": true
        }
    },
    "reporting": {
        "formats": ["json", "html", "console"],
        "include_charts": true,
        "include_recommendations": true,
        "include_performance_metrics": true,
        "output_detailed_reports": true,
        "export_summary_only": false
    },
    "performance": {
        "max_total_time": 1200,
        "memory_limit_mb": 3072,
        "parallel_execution": true,
        "max_concurrent_tools": 4,
        "progress_update_interval": 1.0,
        "enable_memory_monitoring": true,
        "enable_cpu_monitoring": true
    },
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 1,
            "severity": "major",
            "enforce": true,
            "description": "Maximum 1 monolithic module allowed in staging"
        },
        "naming_conventions": {
            "threshold": 92.5,
            "severity": "major",
            "enforce": true,
            "description": "92.5% compliance with naming conventions"
        },
        "test_execution": {
            "threshold": 92.0,
            "severity": "major",
            "enforce": true,
            "description": "92% test pass rate"
        },
        "code_quality": {
            "threshold": 88.0,
            "severity": "major",
            "enforce": true,
            "description": "88% code quality score"
        },
        "performance_score": {
            "threshold": 80.0,
            "severity": "minor",
            "enforce": false,
            "description": "80% performance score threshold"
        }
    },
    "logging": {
        "level": "INFO",
        "enable_file_logging": true,
        "log_file_path": "logs/test_framework.log",
        "max_log_size_mb": 10,
        "backup_count": 5,
        "enable_console_logging": true
    },
    "ci_cd": {
        "enabled": true,
        "fail_on_critical": true,
        "fail_on_major": true,
        "fail_on_minor": false,
        "environment": "staging"
    }
}
EOF
            ;;
        production)
            cat > "$config_file" << EOF
{
    "target_path": ".",
    "output_dir": "reports",
    "tools": {
        "monolithic_detector": {
            "enabled": true,
            "threshold": 500,
            "workers": 4,
            "timeout": 300,
            "exclude_dirs": ["__pycache__", ".git", "node_modules", ".venv", "venv"],
            "file_extensions": [".py"],
            "include_subdirectories": true
        },
        "naming_validator": {
            "enabled": true,
            "workers": 4,
            "min_compliance": 95.0,
            "timeout": 300,
            "check_case": true,
            "check_underscores": true,
            "exclude_patterns": ["test_", "Test", "conftest.py", "setup.py"]
        },
        "unified_test_runner": {
            "enabled": true,
            "parallel_suites": true,
            "max_workers": 4,
            "timeout": 1800,
            "test_patterns": ["test_*.py", "*_test.py"],
            "coverage_threshold": 85.0,
            "fail_fast": true
        },
        "code_quality_validator": {
            "enabled": true,
            "parallel_execution": true,
            "timeout": 600,
            "black_format": true,
            "pylint_check": true,
            "max_line_length": 88,
            "ignore_patterns": ["__pycache__/*", ".git/*"]
        },
        "quality_gate_enforcer": {
            "enabled": true,
            "parallel": true,
            "timeout": 300,
            "enforce_monolithic_gates": true,
            "enforce_naming_gates": true,
            "enforce_test_gates": true,
            "enforce_quality_gates": true
        }
    },
    "reporting": {
        "formats": ["json", "html", "console"],
        "include_charts": true,
        "include_recommendations": true,
        "include_performance_metrics": true,
        "output_detailed_reports": true,
        "export_summary_only": false
    },
    "performance": {
        "max_total_time": 900,
        "memory_limit_mb": 2048,
        "parallel_execution": true,
        "max_concurrent_tools": 3,
        "progress_update_interval": 1.0,
        "enable_memory_monitoring": true,
        "enable_cpu_monitoring": true
    },
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 0,
            "severity": "critical",
            "enforce": true,
            "description": "No monolithic modules allowed in production"
        },
        "naming_conventions": {
            "threshold": 95.0,
            "severity": "critical",
            "enforce": true,
            "description": "95% compliance with naming conventions"
        },
        "test_execution": {
            "threshold": 95.0,
            "severity": "critical",
            "enforce": true,
            "description": "95% test pass rate"
        },
        "code_quality": {
            "threshold": 90.0,
            "severity": "critical",
            "enforce": true,
            "description": "90% code quality score"
        },
        "performance_score": {
            "threshold": 85.0,
            "severity": "major",
            "enforce": true,
            "description": "85% performance score threshold"
        }
    },
    "logging": {
        "level": "INFO",
        "enable_file_logging": true,
        "log_file_path": "logs/test_framework.log",
        "max_log_size_mb": 10,
        "backup_count": 5,
        "enable_console_logging": true
    },
    "ci_cd": {
        "enabled": true,
        "fail_on_critical": true,
        "fail_on_major": true,
        "fail_on_minor": true,
        "environment": "production"
    }
}
EOF
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            return 1
            ;;
    esac
    
    log_success "Quality gates configured for $ENVIRONMENT environment"
}

# Setup platform-specific configuration
setup_platform() {
    if [[ -z "$PLATFORM" ]]; then
        log_warning "No platform specified, skipping platform setup"
        return 0
    fi
    
    log_info "Setting up CI/CD configuration for $PLATFORM..."
    
    case $PLATFORM in
        github)
            setup_github_actions
            ;;
        gitlab)
            setup_gitlab_ci
            ;;
        jenkins)
            setup_jenkins
            ;;
        azure)
            setup_azure_devops
            ;;
        *)
            log_error "Unknown platform: $PLATFORM"
            return 1
            ;;
    esac
}

# Setup GitHub Actions
setup_github_actions() {
    log_info "Setting up GitHub Actions configuration..."
    
    local workflow_dir="$PROJECT_ROOT/.github/workflows"
    mkdir -p "$workflow_dir"
    
    # Copy the comprehensive testing workflow if it exists
    if [[ -f "$workflow_dir/comprehensive-testing.yml" ]]; then
        log_debug "GitHub Actions workflow already exists"
    else
        log_warning "GitHub Actions workflow not found at $workflow_dir/comprehensive-testing.yml"
        log_info "Please ensure the workflow file is present"
    fi
    
    # Create additional GitHub specific files
    create_github_files
}

# Create GitHub-specific files
create_github_files() {
    log_debug "Creating GitHub-specific configuration files..."
    
    # Create .gitignore for CI/CD artifacts
    cat > "$PROJECT_ROOT/.gitignore_ci_cd" << 'EOF'
# CI/CD Artifacts
reports/
logs/
*.log
.coverage
htmlcov/
.pytest_cache/
.coverage.*
coverage.xml
*.cover
.hypothesis/

# Temporary files
tmp/
temp/
.tmp/

# Environment files
.env
.env.local
.env.*.local

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
EOF
    
    log_success "GitHub-specific files created"
}

# Setup GitLab CI
setup_gitlab_ci() {
    log_info "Setting up GitLab CI configuration..."
    
    local gitlab_config="$PROJECT_ROOT/.gitlab-ci.yml"
    
    # Create GitLab CI configuration
    cat > "$gitlab_config" << 'EOF'
stages:
  - setup
  - quality
  - test
  - performance
  - gate
  - notify

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  COMPREHENSIVE_TEST_CONFIG: "test_framework_config.json"

cache:
  paths:
    - .cache/pip/
    - venv/

.python_version_matrix:
  parallel:
    matrix:
      - PYTHON_VERSION: ['3.8', '3.9', '3.10', '3.11', '3.12']

setup:
  stage: setup
  image: python:$PYTHON_VERSION
  before_script:
    - python -m pip install --upgrade pip
    - pip install -r requirements.txt
    - pip install -r requirements_testing.txt
  script:
    - python --version
    - pip list
    - python -c "import comprehensive_test_suite; print('Framework imported successfully')"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

code_quality:
  stage: quality
  image: python:$PYTHON_VERSION
  needs: ["setup"]
  script:
    - pip install black pylint mypy bandit safety
    - black --check --diff src/ tests/ || true
    - pylint src/ --output-format=json --reports=yes > pylint_report.json || true
    - mypy src/ --ignore-missing-imports --json-report mypy_report || true
    - bandit -r src/ -f json -o bandit_report.json || true
    - safety check --json --output safety_report.json || true
  artifacts:
    paths:
      - pylint_report.json
      - mypy_report/
      - bandit_report.json
      - safety_report.json
    expire_in: 30 days

comprehensive_test:
  stage: test
  image: python:$PYTHON_VERSION
  needs: ["setup"]
  script:
    - pip install comprehensive_test_suite
    - mkdir -p reports
    - python comprehensive_test_suite.py --config test_framework_config.json --output reports/comprehensive_report --parallel --max-workers 4 --verbose
  artifacts:
    paths:
      - reports/
    expire_in: 30 days

quality_gates:
  stage: gate
  image: python:3.11
  needs: ["comprehensive_test", "code_quality"]
  script:
    - python -c "
      import json
      import glob
      import os
      
      report_files = glob.glob('reports/comprehensive_report.json')
      if not report_files:
          print('No comprehensive reports found!')
          exit(1)
      
      with open(report_files[0], 'r') as f:
          results = json.load(f)
      
      quality = results.get('quality_assessment', {})
      if quality.get('overall_status') == 'FAIL':
          print('Quality gates failed!')
          exit(1)
      else:
          print('All quality gates passed!')
      "
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
EOF
    
    log_success "GitLab CI configuration created"
}

# Setup Jenkins
setup_jenkins() {
    log_info "Setting up Jenkins configuration..."
    
    local jenkins_file="$PROJECT_ROOT/Jenkinsfile"
    
    # Create Jenkinsfile
    cat > "$jenkins_file" << 'EOF'
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        COMPREHENSIVE_TEST_CONFIG = 'test_framework_config.json'
        PIP_CACHE_DIR = "${WORKSPACE}/.cache/pip"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')
        parallelsAlwaysFailFast()
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements_testing.txt
                    pip install comprehensive_test_suite
                    
                    python3 --version
                    python3 -c "import comprehensive_test_suite; print('Framework imported successfully')"
                '''
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Black Formatting') {
                    steps {
                        sh '''
                            pip install black
                            black --check --diff src/ tests/ || true
                        '''
                    }
                }
                
                stage('Pylint Analysis') {
                    steps {
                        sh '''
                            pip install pylint
                            pylint src/ --output-format=json --reports=yes > pylint_report.json || true
                        '''
                    }
                }
            }
        }
        
        stage('Comprehensive Testing') {
            steps {
                sh '''
                    mkdir -p reports
                    python comprehensive_test_suite.py \
                        --config ${COMPREHENSIVE_TEST_CONFIG} \
                        --output reports/comprehensive_report \
                        --parallel \
                        --max-workers 4 \
                        --verbose
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
                }
            }
        }
        
        stage('Quality Gates') {
            steps {
                sh '''
                    python -c "
                    import json
                    import glob
                    import os
                    
                    report_files = glob.glob('reports/comprehensive_report.json')
                    if not report_files:
                        print('No comprehensive reports found!')
                        exit(1)
                    
                    with open(report_files[0], 'r') as f:
                        results = json.load(f)
                    
                    quality = results.get('quality_assessment', {})
                    if quality.get('overall_status') == 'FAIL':
                        print('Quality gates failed!')
                        exit(1)
                    else:
                        print('All quality gates passed!')
                    "
                '''
            }
        }
    }
    
    post {
        always {
            sh 'rm -rf .cache/pip venv/'
            archiveArtifacts artifacts: '**/reports/**, **/*_report.*, **/*.json, **/*.html', allowEmptyArchive: true
        }
        
        success {
            emailext (
                subject: "Build Successful - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "All quality gates passed successfully!",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
        
        failure {
            emailext (
                subject: "Build Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Quality gates failed. Please check the build logs.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
EOF
    
    log_success "Jenkins configuration created"
}

# Setup Azure DevOps
setup_azure_devops() {
    log_info "Setting up Azure DevOps configuration..."
    
    local azure_config="$PROJECT_ROOT/azure-pipelines.yml"
    
    # Create Azure DevOps pipeline configuration
    cat > "$azure_config" << 'EOF'
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    exclude:
      - docs/*
      - '*.md'

pr:
  branches:
    include:
      - main
      - develop

variables:
  PYTHON_VERSION: '3.11'
  PIP_CACHE_DIR: $(Pipeline.Workspace)/.pip
  COMPREHENSIVE_TEST_CONFIG: test_framework_config.json

stages:
- stage: Build
  displayName: 'Build and Test'
  jobs:
  - job: Setup
    displayName: 'Environment Setup'
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
      displayName: 'Use Python $(PYTHON_VERSION)'
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements_testing.txt
        pip install comprehensive_test_suite
      displayName: 'Install dependencies'
    
    - task: Cache@2
      inputs:
        key: 'python | "$(Agent.OS)" | requirements.txt'
        path: $(PIP_CACHE_DIR)
      displayName: 'Cache pip dependencies'

  - job: ComprehensiveTests
    displayName: 'Comprehensive Testing'
    dependsOn: Setup
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
    
    - task: Python@0
      inputs:
        script: |
          mkdir -p reports
          python comprehensive_test_suite.py \
            --config test_framework_config.json \
            --output reports/comprehensive_report \
            --parallel \
            --max-workers 4 \
            --verbose
      displayName: 'Run comprehensive tests'
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFiles: 'reports/**/*_report.json'
        testRunTitle: 'Comprehensive Test Results'
    
    - task: PublishPipelineArtifact@1
      inputs:
        targetPath: 'reports'
        artifact: 'test-reports'
      displayName: 'Publish test reports'

  - job: QualityGates
    displayName: 'Quality Gate Enforcement'
    dependsOn: ComprehensiveTests
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
    
    - task: DownloadPipelineArtifact@2
      inputs:
        targetPath: 'reports'
        artifact: 'test-reports'
    
    - task: Python@0
      inputs:
        script: |
          python -c "
          import json
          import glob
          import os
          
          report_files = glob.glob('reports/comprehensive_report.json')
          if not report_files:
              print('No comprehensive reports found!')
              exit(1)
          
          with open(report_files[0], 'r') as f:
              results = json.load(f)
          
          quality = results.get('quality_assessment', {})
          if quality.get('overall_status') == 'FAIL':
              print('Quality gates failed!')
              exit(1)
          else:
              print('All quality gates passed!')
          "
      displayName: 'Validate quality gates'
EOF
    
    log_success "Azure DevOps configuration created"
}

# Validate the setup
validate_setup() {
    log_info "Validating CI/CD setup..."
    
    local validation_errors=0
    
    # Check if comprehensive test suite is available
    if ! python3 -c "import comprehensive_test_suite" 2>/dev/null; then
        log_error "Comprehensive test suite not available"
        ((validation_errors++))
    else
        log_success "Comprehensive test suite is available"
    fi
    
    # Check if configuration file exists
    if [[ ! -f "$PROJECT_ROOT/test_framework_config.json" ]]; then
        log_error "Configuration file not found: test_framework_config.json"
        ((validation_errors++))
    else
        log_success "Configuration file exists"
    fi
    
    # Check if required directories exist
    local required_dirs=("src" "tests")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
            log_warning "Directory not found: $dir"
        else
            log_debug "Directory exists: $dir"
        fi
    done
    
    # Test basic functionality
    log_debug "Testing basic functionality..."
    if python3 -c "
import json
import sys
try:
    with open('test_framework_config.json', 'r') as f:
        config = json.load(f)
    print('Configuration loaded successfully')
    sys.exit(0)
except Exception as e:
    print(f'Configuration error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "Configuration validation passed"
    else
        log_error "Configuration validation failed"
        ((validation_errors++))
    fi
    
    # Check platform-specific files
    if [[ -n "$PLATFORM" ]]; then
        case $PLATFORM in
            github)
                if [[ -f "$PROJECT_ROOT/.github/workflows/comprehensive-testing.yml" ]]; then
                    log_success "GitHub Actions workflow exists"
                else
                    log_warning "GitHub Actions workflow not found"
                fi
                ;;
            gitlab)
                if [[ -f "$PROJECT_ROOT/.gitlab-ci.yml" ]]; then
                    log_success "GitLab CI configuration exists"
                else
                    log_warning "GitLab CI configuration not found"
                fi
                ;;
            jenkins)
                if [[ -f "$PROJECT_ROOT/Jenkinsfile" ]]; then
                    log_success "Jenkinsfile exists"
                else
                    log_warning "Jenkinsfile not found"
                fi
                ;;
            azure)
                if [[ -f "$PROJECT_ROOT/azure-pipelines.yml" ]]; then
                    log_success "Azure DevOps pipeline exists"
                else
                    log_warning "Azure DevOps pipeline not found"
                fi
                ;;
        esac
    fi
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "Setup validation completed successfully"
        return 0
    else
        log_error "Setup validation completed with $validation_errors errors"
        return 1
    fi
}

# Create additional configuration files
create_additional_configs() {
    log_info "Creating additional configuration files..."
    
    # Create pytest.ini
    cat > "$PROJECT_ROOT/pytest.ini" << 'EOF'
[tool:pytest]
testpaths = tests src
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
    --junit-xml=reports/junit_results.xml
    --json-report --json-report-file=reports/pytest_results.json
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    performance: marks tests as performance tests
filterwarnings =
    ignore::UserWarning
    ignore::DeprecationWarning
EOF
    
    # Create .pylintrc
    cat > "$PROJECT_ROOT/.pylintrc" << 'EOF'
[MASTER]
jobs=4
persistent=yes
unsafe-load-any-extension=no

[MESSAGES CONTROL]
disable=
    C0114,  # missing-module-docstring
    C0115,  # missing-class-docstring
    C0116,  # missing-function-docstring
    R0903,  # too-few-public-methods
    R0913,  # too-many-arguments

[FORMAT]
max-line-length=88
indent-string='    '

[DESIGN]
max-args=7
max-locals=15
max-returns=6
max-branches=12
max-statements=50

[SIMILARITIES]
min-similarity-lines=4
ignore-comments=yes
ignore-docstrings=yes
ignore-imports=no
EOF
    
    # Create pyproject.toml for Black
    cat > "$PROJECT_ROOT/pyproject.toml" << 'EOF'
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
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
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
disallow_untyped_decorators = false
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:"
]
EOF
    
    # Create Makefile for common tasks
    cat > "$PROJECT_ROOT/Makefile" << 'EOF'
.PHONY: help install test lint format clean ci-setup

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements_testing.txt
	pip install -e .

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	pylint src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

ci-setup: ## Setup CI/CD environment
	./scripts/setup-ci-cd.sh --install-deps --configure-gates --validate-setup

clean: ## Clean up
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf reports/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

ci-test: ## Run CI/CD tests
	python comprehensive_test_suite.py --config test_framework_config.json --output reports/ci_test --verbose
EOF
    
    log_success "Additional configuration files created"
}

# Generate usage examples
generate_usage_examples() {
    log_info "Generating usage examples..."
    
    local examples_dir="$PROJECT_ROOT/examples/ci-cd"
    mkdir -p "$examples_dir"
    
    # Create usage examples
    cat > "$examples_dir/README.md" << 'EOF'
# CI/CD Usage Examples

This directory contains examples for using the Comprehensive Testing Framework in various CI/CD environments.

## Quick Start

### GitHub Actions
```bash
# Setup for GitHub Actions
./scripts/setup-ci-cd.sh --platform github --environment production --install-deps --configure-gates

# Run tests locally
python comprehensive_test_suite.py --config test_framework_config.json --output reports/local_test
```

### GitLab CI
```bash
# Setup for GitLab CI
./scripts/setup-ci-cd.sh --platform gitlab --environment staging --install-deps --configure-gates

# The .gitlab-ci.yml file will be automatically created
```

### Jenkins
```bash
# Setup for Jenkins
./scripts/setup-ci-cd.sh --platform jenkins --environment development --install-deps --configure-gates

# The Jenkinsfile will be automatically created
```

### Azure DevOps
```bash
# Setup for Azure DevOps
./scripts/setup-ci-cd.sh --platform azure --environment production --install-deps --configure-gates

# The azure-pipelines.yml file will be automatically created
```

## Environment-Specific Configurations

### Development
- Lenient quality gates
- Extended timeouts
- More parallel workers
- Detailed logging

### Staging
- Moderate quality gates
- Standard timeouts
- Balanced parallelization
- Standard logging

### Production
- Strict quality gates
- Conservative timeouts
- Limited parallelization
- Minimal logging

## Quality Gates

### Critical Gates (Always Block)
- Monolithic modules: 0 violations
- Test execution: ≥95% success rate

### Major Gates (Block by Default)
- Naming conventions: ≥95% compliance
- Code quality: ≥90% compliance

### Minor Gates (Warning Only)
- Performance score: ≥80% threshold

## Troubleshooting

### Common Issues

1. **Python version compatibility**
   ```bash
   # Check Python version
   python3 --version
   
   # Install specific version
   ./scripts/setup-ci-cd.sh --python-version 3.11
   ```

2. **Missing dependencies**
   ```bash
   # Reinstall dependencies
   ./scripts/setup-ci-cd.sh --install-deps