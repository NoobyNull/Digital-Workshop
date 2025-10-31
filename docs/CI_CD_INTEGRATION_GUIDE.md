# CI/CD Integration Guide

**Version**: 1.0.0  
**Date**: 2025-10-31  
**Status**: Production Ready

## Overview

This guide provides comprehensive instructions for integrating the Comprehensive Testing Framework with popular CI/CD platforms. It covers GitHub Actions, GitLab CI, Jenkins, Azure DevOps, and includes automated setup scripts for quick deployment.

## Table of Contents

1. [GitHub Actions Integration](#github-actions-integration)
2. [GitLab CI Configuration](#gitlab-ci-configuration)
3. [Jenkins Pipeline Setup](#jenkins-pipeline-setup)
4. [Azure DevOps Configuration](#azure-devops-configuration)
5. [Quality Gates Setup](#quality-gates-setup)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Advanced Configuration](#advanced-configuration)
8. [Monitoring and Alerts](#monitoring-and-alerts)

---

## GitHub Actions Integration

### Overview

The Comprehensive Testing Framework includes a pre-configured GitHub Actions workflow (`.github/workflows/comprehensive-testing.yml`) that provides:

- **Multi-Python Support**: Testing across Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Matrix Builds**: Parallel execution across multiple environments
- **Quality Gates**: Automated enforcement of all quality thresholds
- **Artifact Collection**: Comprehensive test reports and quality metrics
- **Notifications**: Automated reporting to Slack/Teams/Email
- **Branch Protection**: Quality gates for protected branches

### Features

#### Automated Testing Pipeline

```yaml
# Triggers
on:
  push:
    branches: [ main, develop, 'feature/*', 'hotfix/*' ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:
    inputs:
      test_level: [quick, standard, full, performance]
      python_version: ['3.8', '3.9', '3.10', '3.11', '3.12']
```

#### Quality Gate Enforcement

The workflow enforces the following quality gates:

| Gate | Threshold | Severity | Action |
|------|-----------|----------|--------|
| **Monolithic Modules** | 0 violations | Critical | Block deployment |
| **Naming Conventions** | ≥95% compliance | Major | Block deployment |
| **Test Execution** | ≥95% success rate | Critical | Block deployment |
| **Code Quality** | ≥90% compliance | Major | Block deployment |

#### Job Structure

1. **Setup**: Environment preparation and dependency installation
2. **Code Quality**: Static analysis with Black, Pylint, MyPy, Bandit
3. **Comprehensive Tests**: Full framework execution
4. **Performance Tests**: Benchmarking and memory leak detection
5. **Multi-Python Testing**: Cross-version compatibility
6. **Quality Gates**: Automated enforcement and validation
7. **Notifications**: Results reporting and alerts

### Setup Instructions

#### 1. Repository Configuration

The workflow is automatically enabled when the workflow file is present in `.github/workflows/`. No additional setup is required.

#### 2. Required Secrets (Optional)

For enhanced notifications, configure these secrets in your repository:

```bash
# Slack integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Microsoft Teams integration
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK

# Email notifications (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### 3. Branch Protection Rules

Configure branch protection for critical branches:

1. Go to repository Settings > Branches
2. Add rule for `main` branch
3. Require status checks to pass before merging
4. Require comprehensive testing workflow to pass

### Workflow Customization

#### Modify Test Levels

Edit the workflow file to adjust test levels:

```yaml
strategy:
  matrix:
    test-level: [quick, standard, full]
    include:
      - test-level: quick
        timeout-minutes: 10
        parallel-workers: 2
      - test-level: standard
        timeout-minutes: 20
        parallel-workers: 4
      - test-level: full
        timeout-minutes: 45
        parallel-workers: 4
```

#### Adjust Quality Thresholds

Modify quality gate thresholds in the workflow:

```yaml
quality_gates:
  monolithic_modules:
    threshold: 0
    severity: critical
  naming_conventions:
    threshold: 95.0
    severity: major
  test_execution:
    threshold: 95.0
    severity: critical
  code_quality:
    threshold: 90.0
    severity: major
```

---

## GitLab CI Configuration

### Overview

GitLab CI provides native integration with the Comprehensive Testing Framework through `.gitlab-ci.yml` configuration.

### Configuration Example

```yaml
# .gitlab-ci.yml
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

# Cache pip dependencies
cache:
  paths:
    - .cache/pip/
    - venv/

# Python version matrix
.python_version_matrix:
  parallel:
    matrix:
      - PYTHON_VERSION: ['3.8', '3.9', '3.10', '3.11', '3.12']

# Setup stage
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
  artifacts:
    reports:
      dotenv: build.env

# Code quality validation
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
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# Comprehensive testing
comprehensive_test:
  stage: test
  image: python:$PYTHON_VERSION
  needs: ["setup"]
  script:
    - pip install comprehensive_test_suite
    - mkdir -p reports
    - python comprehensive_test_suite.py
      --config test_framework_config.json
      --output reports/comprehensive_report
      --parallel
      --max-workers 4
      --verbose
  artifacts:
    paths:
      - reports/
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# Performance testing
performance_test:
  stage: performance
  image: python:$PYTHON_VERSION
  needs: ["setup"]
  script:
    - pip install memory-profiler psutil
    - python -c "
      import psutil
      import time
      process = psutil.Process()
      initial_memory = process.memory_info().rss / 1024 / 1024
      print(f'Initial memory: {initial_memory:.2f} MB')
      
      # Simulate workload
      for i in range(1000):
          _ = [j**2 for j in range(1000)]
      
      final_memory = process.memory_info().rss / 1024 / 1024
      memory_increase = final_memory - initial_memory
      print(f'Memory increase: {memory_increase:.2f} MB')
      
      if memory_increase > 100:
          print('WARNING: High memory usage!')
          exit(1)
      "
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - when: manual

# Quality gates enforcement
quality_gates:
  stage: gate
  image: python:3.11
  needs: ["comprehensive_test", "code_quality"]
  script:
    - |
      python -c "
      import json
      import glob
      import os
      
      # Find comprehensive report
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

# Notifications
notify_failure:
  stage: notify
  image: alpine:latest
  needs: ["quality_gates"]
  script:
    - |
      if [ "$CI_JOB_STATUS" = "failed" ]; then
        echo "Pipeline failed - sending notifications"
        # Add your notification logic here
      fi
  rules:
    - if: $CI_JOB_STATUS == "failed"
      when: always
  when: always
```

### GitLab CI Features

#### Merge Request Integration

```yaml
# Automatic MR validation
validate_merge_request:
  stage: validate
  script:
    - python comprehensive_test_suite.py --config test_framework_config.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  artifacts:
    reports:
      junit: reports/junit_results.xml
```

#### Scheduled Pipelines

```yaml
# Daily comprehensive testing
nightly_test:
  stage: test
  script:
    - python comprehensive_test_suite.py --config test_framework_config.json --full
  rules:
    - when: schedule
      cron: "0 2 * * *"
```

---

## Jenkins Pipeline Setup

### Overview

Jenkins provides flexible pipeline configuration through `Jenkinsfile` with both declarative and scripted syntax.

### Declarative Pipeline Configuration

```groovy
// Jenkinsfile
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
            parallel {
                stage('Python Setup') {
                    steps {
                        script {
                            def pythonVersions = ['3.8', '3.9', '3.10', '3.11', '3.12']
                            def setupJobs = [:]
                            
                            pythonVersions.each { version ->
                                setupJobs["python-${version}"] = { ->
                                    node('linux') {
                                        stage("Setup Python ${version}") {
                                            sh """
                                                python${version} -m pip install --upgrade pip
                                                pip${version} install -r requirements.txt
                                                pip${version} install -r requirements_testing.txt
                                                pip${version} install comprehensive_test_suite
                                                
                                                python${version} --version
                                                python${version} -c "import comprehensive_test_suite; print('Framework imported successfully')"
                                            """
                                        }
                                    }
                                }
                            }
                            
                            parallel setupJobs
                        }
                    }
                }
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
                    post {
                        always {
                            archiveArtifacts artifacts: 'black_report.txt', allowEmptyArchive: true
                        }
                    }
                }
                
                stage('Pylint Analysis') {
                    steps {
                        sh '''
                            pip install pylint
                            pylint src/ --output-format=json --reports=yes > pylint_report.json || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'pylint_report.json', allowEmptyArchive: true
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: '.',
                                reportFiles: 'pylint_report.json',
                                reportName: 'Pylint Report'
                            ])
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        sh '''
                            pip install bandit safety
                            bandit -r src/ -f json -o bandit_report.json || true
                            safety check --json --output safety_report.json || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit_report.json,safety_report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Comprehensive Testing') {
            matrix {
                axes {
                    axis {
                        name 'TEST_LEVEL'
                        values 'quick', 'standard', 'full'
                    }
                }
                agent any
                stages {
                    stage("${TEST_LEVEL}") {
                        steps {
                            sh """
                                mkdir -p reports
                                python comprehensive_test_suite.py \\
                                    --config ${COMPREHENSIVE_TEST_CONFIG} \\
                                    --output reports/comprehensive_report \\
                                    --${TEST_LEVEL} \\
                                    --parallel \\
                                    --max-workers 4
                            """
                        }
                        post {
                            always {
                                archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
                                publishTestResults testResultsPattern: 'reports/junit_results.xml'
                            }
                        }
                    }
                }
            }
        }
        
        stage('Performance Testing') {
            when {
                anyOf {
                    branch 'main'
                    buildingTag()
                }
            }
            steps {
                sh '''
                    pip install memory-profiler psutil
                    
                    # Memory usage test
                    python -c "
                    import psutil
                    import time
                    process = psutil.Process()
                    initial_memory = process.memory_info().rss / 1024 / 1024
                    print(f'Initial memory: {initial_memory:.2f} MB')
                    
                    # Simulate workload
                    for i in range(1000):
                        _ = [j**2 for j in range(1000)]
                    
                    final_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = final_memory - initial_memory
                    print(f'Memory increase: {memory_increase:.2f} MB')
                    
                    if memory_increase > 100:
                        print('WARNING: High memory usage!')
                        exit(1)
                    "
                    
                    # Execution time test
                    time python comprehensive_test_suite.py --config test_framework_config.json --sequential
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'performance_report.*', allowEmptyArchive: true
                }
            }
        }
        
        stage('Quality Gates') {
            steps {
                script {
                    def gateResults = sh(
                        script: '''
                            python -c "
                            import json
                            import glob
                            import os
                            
                            # Find comprehensive report
                            report_files = glob.glob('reports/comprehensive_report.json')
                            if not report_files:
                                print('No comprehensive reports found!')
                                exit(1)
                            
                            with open(report_files[0], 'r') as f:
                                results = json.load(f)
                            
                            quality = results.get('quality_assessment', {})
                            summary = results.get('execution_summary', {})
                            
                            print(f'Overall Status: {quality.get(\\"overall_status\\", \\"UNKNOWN\\")}')
                            print(f'Compliance: {summary.get(\\"overall_compliance\\", 0):.1f}%')
                            
                            if quality.get('overall_status') == 'FAIL':
                                print('Quality gates failed!')
                                exit(1)
                            else:
                                print('All quality gates passed!')
                            "
                        ''',
                        returnStatus: true
                    )
                    
                    if (gateResults != 0) {
                        currentBuild.result = 'FAILURE'
                        error("Quality gates failed - blocking deployment")
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Cleanup
                sh 'rm -rf .cache/pip venv/'
                
                // Archive all reports
                archiveArtifacts artifacts: '**/reports/**, **/*_report.*, **/*.json, **/*.html', allowEmptyArchive: true
            }
        }
        
        success {
            script {
                // Notify on success
                emailext (
                    subject: "Build Successful - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                    body: """
                        <h3>Build Successful</h3>
                        <p><b>Job:</b> ${env.JOB_NAME}</p>
                        <p><b>Build:</b> ${env.BUILD_NUMBER}</p>
                        <p><b>Branch:</b> ${env.BRANCH_NAME}</p>
                        <p><b>Commit:</b> ${env.GIT_COMMIT}</p>
                        <p><b>URL:</b> <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>All quality gates passed successfully!</p>
                    """,
                    to: "${env.CHANGE_AUTHOR_EMAIL}",
                    recipientProviders: [developers(), requestor()]
                )
            }
        }
        
        failure {
            script {
                // Notify on failure
                emailext (
                    subject: "Build Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                    body: """
                        <h3>Build Failed</h3>
                        <p><b>Job:</b> ${env.JOB_NAME}</p>
                        <p><b>Build:</b> ${env.BUILD_NUMBER}</p>
                        <p><b>Branch:</b> ${env.BRANCH_NAME}</p>
                        <p><b>Commit:</b> ${env.GIT_COMMIT}</p>
                        <p><b>URL:</b> <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                        <p>Quality gates failed. Please check the build logs.</p>
                    """,
                    to: "${env.CHANGE_AUTHOR_EMAIL}",
                    recipientProviders: [developers(), requestor()]
                )
            }
        }
    }
}
```

### Scripted Pipeline Configuration

```groovy
// Alternative scripted Jenkinsfile
node('linux') {
    try {
        stage('Checkout') {
            checkout scm
        }
        
        stage('Setup Environment') {
            sh '''
                python3 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                pip install -r requirements_testing.txt
                pip install comprehensive_test_suite
            '''
        }
        
        stage('Run Comprehensive Tests') {
            script {
                def testResults = sh(
                    script: '''
                        source venv/bin/activate
                        mkdir -p reports
                        python comprehensive_test_suite.py \\
                            --config test_framework_config.json \\
                            --output reports/comprehensive_report \\
                            --parallel \\
                            --verbose
                    ''',
                    returnStatus: true
                )
                
                if (testResults != 0) {
                    throw new Exception("Comprehensive tests failed")
                }
            }
        }
        
        stage('Quality Gate Validation') {
            sh '''
                source venv/bin/activate
                python -c "
                import json
                with open('reports/comprehensive_report.json') as f:
                    results = json.load(f)
                
                if results['quality_assessment']['overall_status'] == 'FAIL':
                    print('Quality gates failed!')
                    exit(1)
                print('All quality gates passed!')
                "
            '''
        }
        
        currentBuild.result = 'SUCCESS'
        
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        stage('Cleanup') {
            sh 'rm -rf venv/ .cache/'
        }
    }
}
```

### Jenkins Configuration Requirements

#### Required Plugins

1. **Pipeline**: For pipeline syntax support
2. **Git**: For source control integration
3. **Workspace Cleanup**: For workspace management
4. **HTML Publisher**: For test report publishing
5. **Email Extension**: For email notifications
6. **Parallel Test Executor**: For parallel test execution

#### Global Configuration

```groovy
// In Jenkins Global Configuration (Manage Jenkins > Configure System)
def globalConfig = """
pipeline {
    agent any
    environment {
        PYTHONUNBUFFERED = '1'
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
    }
    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 60, unit: 'MINUTES')
    }
}
"""
```

---

## Azure DevOps Configuration

### Overview

Azure DevOps provides CI/CD integration through `azure-pipelines.yml` with comprehensive testing framework support.

### Configuration Example

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
      - features/*
      - hotfix/*
  paths:
    exclude:
      - docs/*
      - '*.md'

pr:
  branches:
    include:
      - main
      - develop
  paths:
    exclude:
      - docs/*
      - '*.md'

schedules:
- cron: "0 2 * * *"
  displayName: Daily comprehensive test
  branches:
    include:
    - main
  always: true

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
    
    - script: |
        python --version
        pip list
        python -c "import comprehensive_test_suite; print('Framework imported successfully')"
      displayName: 'Verify installation'
    
    - task: Cache@2
      inputs:
        key: 'python | "$(Agent.OS)" | requirements.txt'
        path: $(PIP_CACHE_DIR)
      displayName: 'Cache pip dependencies'

  - job: CodeQuality
    displayName: 'Code Quality Analysis'
    dependsOn: Setup
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
    
    - script: |
        pip install black pylint mypy bandit safety
      displayName: 'Install quality tools'
    
    - task: Python@0
      inputs:
        script: |
          black --check --diff src/ tests/
      displayName: 'Black formatting check'
      continueOnError: true
    
    - task: Python@0
      inputs:
        script: |
          pylint src/ --output-format=json --reports=yes > pylint_report.json
      displayName: 'Pylint analysis'
      continueOnError: true
    
    - task: Python@0
      inputs:
        script: |
          mypy src/ --ignore-missing-imports --json-report mypy_report
      displayName: 'MyPy type checking'
      continueOnError: true
    
    - task: Python@0
      inputs:
        script: |
          bandit -r src/ -f json -o bandit_report.json
      displayName: 'Bandit security scan'
      continueOnError: true
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFiles: '**/bandit_report.json'
        testRunTitle: 'Security Scan Results'
    
    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: Cobertura
        summaryFileLocation: '**/coverage.xml'
      displayName: 'Publish code coverage'

  - job: ComprehensiveTests
    displayName: 'Comprehensive Testing'
    dependsOn: Setup
    strategy:
      matrix:
        Quick:
          TEST_LEVEL: quick
          TIMEOUT_MINUTES: 10
          WORKERS: 2
        Standard:
          TEST_LEVEL: standard
          TIMEOUT_MINUTES: 20
          WORKERS: 4
        Full:
          TEST_LEVEL: full
          TIMEOUT_MINUTES: 45
          WORKERS: 4
    pool:
      vmImage: 'ubuntu-latest'
    timeoutInMinutes: $(TIMEOUT_MINUTES)
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
            --$(TEST_LEVEL) \
            --parallel \
            --max-workers $(WORKERS) \
            --verbose
      displayName: 'Run comprehensive tests'
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFiles: 'reports/**/*_report.json'
        testRunTitle: 'Comprehensive Test Results - $(TEST_LEVEL)'
    
    - task: PublishPipelineArtifact@1
      inputs:
        targetPath: 'reports'
        artifact: 'test-reports-$(TEST_LEVEL)'
      displayName: 'Publish test reports'

  - job: PerformanceTests
    displayName: 'Performance Testing'
    dependsOn: Setup
    condition: or(eq(variables['Build.SourceBranch'], 'refs/heads/main'), eq(variables['Build.Reason'], 'Schedule'))
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
    
    - script: |
        pip install memory-profiler psutil
      displayName: 'Install performance tools'
    
    - task: Python@0
      inputs:
        script: |
          python -c "
          import psutil
          import time
          process = psutil.Process()
          initial_memory = process.memory_info().rss / 1024 / 1024
          print(f'Initial memory: {initial_memory:.2f} MB')
          
          # Simulate workload
          for i in range(1000):
              _ = [j**2 for j in range(1000)]
          
          final_memory = process.memory_info().rss / 1024 / 1024
          memory_increase = final_memory - initial_memory
          print(f'Memory increase: {memory_increase:.2f} MB')
          
          if memory_increase > 100:
              print('WARNING: High memory usage!')
              exit(1)
          "
      displayName: 'Memory usage test'
    
    - task: Python@0
      inputs:
        script: |
          time python comprehensive_test_suite.py --config test_framework_config.json --sequential
      displayName: 'Execution time test'
    
    - task: PublishPipelineArtifact@1
      inputs:
        targetPath: 'performance_report.*'
        artifact: 'performance-reports'
      displayName: 'Publish performance reports'

  - job: QualityGates
    displayName: 'Quality Gate Enforcement'
    dependsOn: [ComprehensiveTests, CodeQuality]
    pool:
      vmImage: 'ubuntu-latest'
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(PYTHON_VERSION)'
    
    - task: DownloadPipelineArtifact@2
      inputs:
        targetPath: 'reports'
        artifact: 'test-reports-Standard'
    
    - task: Python@0
      inputs:
        script: |
          python -c "
          import json
          import glob
          import os
          
          # Find comprehensive report
          report_files = glob.glob('reports/comprehensive_report.json')
          if not report_files:
              print('No comprehensive reports found!')
              exit(1)
          
          with open(report_files[0], 'r') as f:
              results = json.load(f)
          
          quality = results.get('quality_assessment', {})
          summary = results.get('execution_summary', {})
          
          print(f'Overall Status: {quality.get(\\"overall_status\\", \\"UNKNOWN\\")}')
          print(f'Compliance: {summary.get(\\"overall_compliance\\", 0):.1f}%')
          
          if quality.get('overall_status') == 'FAIL':
              print('Quality gates failed!')
              exit(1)
          else:
              print('All quality gates passed!')
          "
      displayName: 'Validate quality gates'
    
    - task: PublishTestResults@2
      condition: always()
      inputs:
        testResultsFiles: '**/quality_gate_report.json'
        testRunTitle: 'Quality Gate Results'

- stage: Deploy
  displayName: 'Deploy'
  dependsOn: Build
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: DeployToProduction
    displayName: 'Deploy to Production'
    pool:
      vmImage: 'ubuntu-latest'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: |
              echo "Deploying to production..."
              # Add your deployment steps here
            displayName: 'Deploy application'

# Notifications
notifications:
- event: buildCompletion
    templateName: 'Build Completion'
    conditions:
    - completed
    - failed
```

### Azure DevOps Features

#### Release Pipeline Integration

```yaml
# release-pipeline.yml
stages:
- stage: QA
  jobs:
  - deployment: ComprehensiveTests
    environment: 'QA'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: Python@0
            inputs:
              script: |
                python comprehensive_test_suite.py \
                  --config test_framework_config.json \
                  --output reports/qa_report \
                  --full
          - task: PublishTestResults@2
            inputs:
              testResultsFiles: 'reports/**/*_report.json'

- stage: Production
  dependsOn: QA
  condition: succeeded()
  jobs:
  - deployment: DeployProduction
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: |
              echo "Production deployment approved and completed"
```

#### Service Connection Configuration

```yaml
# Service connection for notifications
- task: SendEmail@2
  inputs:
    To: '$(Build.RequestedForEmail)'
    Subject: 'Build $(Build.BuildNumber) - $(Agent.JobStatus)'
    Body: |
      Build Status: $(Agent.JobStatus)
      Pipeline: $(Build.DefinitionName)
      Branch: $(Build.SourceBranch)
      Commit: $(Build.SourceVersion)
      URL: $(System.TeamFoundationCollectionUri)$(System.TeamProject)/_build/results?buildId=$(Build.BuildId)
  condition: always()
```

---

## Quality Gates Setup

### Overview

Quality gates provide automated enforcement of code quality standards before deployment. The Comprehensive Testing Framework includes configurable gates with different severity levels.

### Quality Gate Configuration

#### Default Quality Gates

```json
{
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 0,
            "severity": "critical",
            "enforce": true,
            "description": "No monolithic modules allowed",
            "auto_fix": false
        },
        "naming_conventions": {
            "threshold": 95.0,
            "severity": "major", 
            "enforce": true,
            "description": "95% compliance with naming conventions",
            "auto_fix": false
        },
        "test_execution": {
            "threshold": 95.0,
            "severity": "critical",
            "enforce": true,
            "description": "95% test pass rate",
            "auto_fix": false
        },
        "code_quality": {
            "threshold": 90.0,
            "severity": "major",
            "enforce": true,
            "description": "90% code quality score",
            "auto_fix": true
        },
        "performance_score": {
            "threshold": 80.0,
            "severity": "minor",
            "enforce": false,
            "description": "80% performance score threshold",
            "auto_fix": false
        }
    }
}
```

#### Environment-Specific Gates

**Development Environment** (lenient thresholds):

```json
{
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 2,
            "severity": "major"
        },
        "naming_conventions": {
            "threshold": 90.0,
            "severity": "minor"
        },
        "test_execution": {
            "threshold": 85.0,
            "severity": "major"
        },
        "code_quality": {
            "threshold": 85.0,
            "severity": "minor"
        }
    }
}
```

**Production Environment** (strict thresholds):

```json
{
    "quality_gates": {
        "monolithic_modules": {
            "threshold": 0,
            "severity": "critical"
        },
        "naming_conventions": {
            "threshold": 98.0,
            "severity": "critical"
        },
        "test_execution": {
            "threshold": 98.0,
            "severity": "critical"
        },
        "code_quality": {
            "threshold": 95.0,
            "severity": "critical"
        },
        "performance_score": {
            "threshold": 90.0,
            "severity": "major"
        }
    }
}
```

### Gate Enforcement Logic

#### Critical Gates (Block Deployment)

- **Monolithic Modules**: Any violations block deployment
- **Test Execution**: <95% success rate blocks deployment

#### Major Gates (Block Deployment by Default)

- **Naming Conventions**: <95% compliance blocks deployment
- **Code Quality**: <90% compliance blocks deployment

#### Minor Gates (Warning Only)

- **Performance Score**: <80% performance generates warning

### Custom Quality Gate Implementation

#### Adding New Quality Gates

```python
# custom_quality_gate.py
import json
from typing import Dict, Any, List

class CustomQualityGate:
    """Custom quality gate implementation."""
    
    def __init__(self, gate_name: str, config: Dict[str, Any]):
        self.gate_name = gate_name
        self.config = config
        self.threshold = config.get('threshold', 0.0)
        self.severity = config.get('severity', 'minor')
        self.enforce = config.get('enforce', True)
        self.description = config.get('description', '')
    
    def evaluate(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate quality gate against metrics."""
        actual_value = self._get_actual_value(metrics)
        passed = self._check_threshold(actual_value)
        
        result = {
            'gate_name': self.gate_name,
            'passed': passed,
            'actual_value': actual_value,
            'threshold': self.threshold,
            'severity': self.severity,
            'enforced': self.enforce,
            'description': self.description
        }
        
        if not passed and self.enforce:
            result['blocking'] = self.severity in ['critical', 'major']
            result['recommendations'] = self._generate_recommendations(actual_value)
        
        return result
    
    def _get_actual_value(self, metrics: Dict[str, Any]) -> float:
        """Extract actual value from metrics."""
        # Implement metric extraction logic
        return metrics.get(self.gate_name, 0.0)
    
    def _check_threshold(self, actual_value: float) -> bool:
        """Check if actual value meets threshold."""
        return actual_value >= self.threshold
    
    def _generate_recommendations(self, actual_value: float) -> List[str]:
        """Generate recommendations for improvement."""
        return [f"Improve {self.gate_name} from {actual_value:.1f} to {self.threshold:.1f}"]

# Usage example
gate_config = {
    'threshold': 95.0,
    'severity': 'major',
    'enforce': True,
    'description': 'Custom metric threshold'
}

gate = CustomQualityGate('custom_metric', gate_config)
result = gate.evaluate({'custom_metric': 87.5})
```

#### Gate Evaluation Engine

```python
# quality_gate_engine.py
import json
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class GateResult:
    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    severity: str
    blocking: bool
    recommendations: List[str]

class QualityGateEngine:
    """Quality gate evaluation engine."""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.gates_config = self.config.get('quality_gates', {})
    
    def evaluate_all_gates(self, metrics: Dict[str, Any]) -> List[GateResult]:
        """Evaluate all configured quality gates."""
        results = []
        
        for gate_name, gate_config in self.gates_config.items():
            result = self._evaluate_gate(gate_name, gate_config, metrics)
            results.append(result)
        
        return results
    
    def _evaluate_gate(self, gate_name: str, gate_config: Dict[str, Any], 
                      metrics: Dict[str, Any]) -> GateResult:
        """Evaluate a single quality gate."""
        threshold = gate_config.get('threshold', 0.0)
        severity = gate_config.get('severity', 'minor')
        enforce = gate_config.get('enforce', True)
        
        # Get actual value (customize based on gate type)
        actual_value = self._extract_metric_value(gate_name, metrics)
        
        # Check threshold
        passed = actual_value >= threshold
        
        # Determine if blocking
        blocking = enforce and severity in ['critical', 'major']
        
        # Generate recommendations
        recommendations = []
        if not passed:
            recommendations = self._generate_gate_recommendations(
                gate_name, actual_value, threshold, severity
            )
        
        return GateResult(
            gate_name=gate_name,
            passed=passed,
            actual_value=actual_value,
            threshold=threshold,
            severity=severity,
            blocking=blocking,
            recommendations=recommendations
        )
    
    def _extract_metric_value(self, gate_name: str, metrics: Dict[str, Any]) -> float:
        """Extract metric value for gate."""
        metric_mapping = {
            'monolithic_modules': lambda m: m.get('monolithic_files_found', 0),
            'naming_conventions': lambda m: m.get('compliance_rate', 0.0),
            'test_execution': lambda m: m.get('success_rate', 0.0),
            'code_quality': lambda m: m.get('overall_compliance', 0.0),
            'performance_score': lambda m: m.get('performance_score', 0.0)
        }
        
        extractor = metric_mapping.get(gate_name, lambda m: 0.0)
        return extractor(metrics)
    
    def _generate_gate_recommendations(self, gate_name: str, actual: float, 
                                     threshold: float, severity: str) -> List[str]:
        """Generate recommendations for gate improvement."""
        recommendations = []
        
        if gate_name == 'monolithic_modules':
            recommendations.append("Refactor monolithic modules into smaller, focused components")
            recommendations.append("Apply single responsibility principle")
            
        elif gate_name == 'naming_conventions':
            recommendations.append("Review and rename files to follow naming conventions")
            recommendations.append("Use consistent case (snake_case for Python files)")
            
        elif gate_name == 'test_execution':
            recommendations.append("Fix failing tests")
            recommendations.append("Add missing test cases for uncovered functionality")
            
        elif gate_name == 'code_quality':
            recommendations.append("Address linting violations")
            recommendations.append("Improve code formatting and structure")
            
        elif gate_name == 'performance_score':
            recommendations.append("Optimize slow-running code")
            recommendations.append("Reduce memory usage and improve efficiency")
        
        return recommendations
    
    def should_block_deployment(self, results: List[GateResult]) -> tuple:
        """Determine if deployment should be blocked."""
        blocking_gates = [r for r in results if r.blocking and not r.passed]
        
        if blocking_gates:
            return True, blocking_gates
        
        return False, []

# Usage example
engine = QualityGateEngine('test_framework_config.json')
metrics = {
    'monolithic_files_found': 0,
    'compliance_rate': 96.5,
    'success_rate': 97.2,
    'overall_compliance': 91.8,
    'performance_score': 85.4
}

results = engine.evaluate_all_gates(metrics)
should_block, blocking_gates = engine.should_block_deployment(results)

if should_block:
    print(f"Deployment blocked by {len(blocking_gates)} quality gates:")
    for gate in blocking_gates:
        print(f"  - {gate.gate_name}: {gate.actual_value:.1f} (threshold: {gate.threshold:.1f})")
else:
    print("All quality gates passed - deployment approved")
```

### CI/CD Integration

#### GitHub Actions Quality Gate Check

```yaml
- name: Quality Gate Validation
  run: |
    python -c "
    import json
    import sys
    
    with open('reports/comprehensive_report.json') as f:
        results = json.load(f)
    
    quality = results.get('quality_assessment', {})
    if quality.get('overall_status') == 'FAIL':
        print('Quality gates failed!')
        for tool_result in results.get('tool_results', []):
            if not tool_result['success']:
                print(f'  - {tool_result[\"tool_name\"]}: FAILED')
        sys.exit(1)
    else:
        print('All quality gates passed!')
    "
```

#### Jenkins Quality Gate Stage

```groovy
stage('Quality Gates') {
    steps {
        script {
            def gateResults = sh(
                script: '''
                    python quality_gate_engine.py \\
                        --config test_framework_config.json \\
                        --metrics-file reports/comprehensive_report.json \\
                        --output reports/gate_results.json
                ''',
                returnStatus: true
            )
            
            if (gateResults != 0) {
                currentBuild.result = 'UNSTABLE'
                error("Quality gates failed - manual approval required")
            }
        }
    }
}
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Python Version Compatibility

**Problem**: Pipeline fails with Python version errors

**Symptoms**:
```
ERROR: Package requires a different Python: 3.7.0 not in ['>=3.8']
```

**Solution**:
```yaml
# Ensure correct Python version in CI/CD
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'  # Use supported version
```

#### Issue 2: Memory Limitations

**Problem**: Pipeline runs out of memory during testing

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solutions**:
1. **Increase memory limits**:
   ```yaml
   # GitHub Actions
   - name: Run tests
     env:
       MALLOC_ARENA_MAX: 2
     run: python comprehensive_test_suite.py
   ```

2. **Reduce parallel workers**:
   ```json
   {
     "performance": {
       "max_concurrent_tools": 2,
       "memory_limit_mb": 1024
     }
   }
   ```

#### Issue 3: Test Timeouts

**Problem**: Tests timeout in CI/CD environment

**Symptoms**:
```
ERROR: Test execution timed out after 1800 seconds
```

**Solutions**:
1. **Adjust timeout values**:
   ```yaml
   # GitHub Actions
   - name: Run comprehensive tests
     timeout-minutes: 60  # Increase timeout
     run: python comprehensive_test_suite.py
   ```

2. **Use sequential execution**:
   ```bash
   python comprehensive_test_suite.py --sequential
   ```

#### Issue 4: Permission Errors

**Problem**: Cannot write to reports directory

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: 'reports/'
```

**Solution**:
```bash
# Ensure reports directory exists and is writable
mkdir -p reports
chmod 755 reports
```

#### Issue 5: Dependency Installation Failures

**Problem**: Package installation fails in CI/CD

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement
```

**Solutions**:
1. **Update pip first**:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Use specific versions**:
   ```txt
   # requirements.txt
   comprehensive_test_suite==1.0.0
   pytest>=7.0.0
   ```

### Debug Mode

#### Enable Verbose Logging

```bash
# Run with verbose output
python comprehensive_test_suite.py --verbose

# Enable debug logging
export LOG_LEVEL=DEBUG
python comprehensive_test_suite.py
```

#### Debug Configuration

```json
{
    "logging": {
        "level": "DEBUG",
        "enable_file_logging": true,
        "log_file_path": "logs/debug.log",
        "max_log_size_mb": 50,
        "backup_count": 10
    },
    "performance": {
        "enable_detailed_timing": true,
        "save_intermediate_results": true
    }
}
```

### Log Analysis

#### Common Log Patterns

**Successful Execution**:
```
2025-10-31 20:00:00 - INFO - Starting execution of 5 tools
2025-10-31 20:00:01 - INFO - Tool monolithic_detector completed in 15.23s
2025-10-31 20:00:02 - INFO - Tool naming_validator completed in 12.45s
2025-10-31 20:00:03 - INFO - All tools completed successfully
```

**Quality Gate Failure**:
```
2025-10-31 20:00:00 - ERROR - Quality gate 'naming_conventions' failed: 87.5% < 95.0%
2025-10-31 20:00:00 - ERROR - Deployment blocked by quality gates
```

**Performance Issues**:
```
2025-10-31 20:00:00 - WARNING - Memory usage exceeded limit: 2.1GB > 2.0GB
2025-10-31 20:00:01 - WARNING - Execution time exceeded threshold: 950s > 900s
```

### Performance Optimization

#### Optimize for CI/CD Environments

```json
{
    "performance": {
        "max_total_time": 600,  # 10 minutes for CI/CD
        "memory_limit_mb": 1024,  # 1GB for CI/CD
        "parallel_execution": true,
        "max_concurrent_tools": 2,  # Conservative for CI/CD
        "progress_update_interval": 0.5,
        "enable_memory_monitoring": true
    },
    "tools": {
        "monolithic_detector": {
            "timeout": 180,  # 3 minutes
            "workers": 2
        },
        "naming_validator": {
            "timeout": 180,
            "workers": 2
        },
        "unified_test_runner": {
            "timeout": 900,  # 15 minutes
            "max_workers": 2
        }
    }
}
```

#### Resource Monitoring

```bash
# Monitor resource usage
top -p $(pgrep -f comprehensive_test_suite)

# Check memory usage
ps aux | grep comprehensive_test_suite

# Monitor disk usage
du -sh reports/
```

---

## Advanced Configuration

### Custom Tool Integration

#### Adding External Tools

```python
# custom_tool_integration.py
import subprocess
import json
from typing import Dict, Any

class ExternalToolIntegrator:
    """Integrate external tools with comprehensive testing framework."""
    
    def __init__(self, tool_config: Dict[str, Any]):
        self.tool_config = tool_config
        self.tools = tool_config.get('external_tools', {})
    
    def run_sonarqube_analysis(self) -> Dict[str, Any]:
        """Run SonarQube analysis."""
        cmd = [
            'sonar-scanner',
            '-Dsonar.projectKey=my_project',
            '-Dsonar.sources=src',
            '-Dsonar.tests=tests',
            '-Dsonar.python.coverage.reportPaths=coverage.xml'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'tool_name': 'sonarqube',
            'success': result.returncode == 0,
            'exit_code': result.returncode,
            'output': result.stdout,
            'error': result.stderr
        }
    
    def run_codeclimate_analysis(self) -> Dict[str, Any]:
        """Run Code Climate analysis."""
        cmd = [
            'codeclimate-test-reporter',
            '--before', 'before.json',
            '--after', 'after.json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'tool_name': 'codeclimate',
            'success': result.returncode == 0,
            'exit_code': result.returncode,
            'output': result.stdout,
            'error': result.stderr
        }
    
    def integrate_all_external_tools(self) -> Dict[str, Any]:
        """Run all configured external tools."""
        results = {}
        
        if 'sonarqube' in self.tools:
            results['sonarqube'] = self.run_sonarqube_analysis()
        
        if 'codeclimate' in self.tools:
            results['codeclimate'] = self.run_codeclimate_analysis()
        
        return results
```

#### Custom Quality Metrics

```python
# custom_quality_metrics.py
import ast
import os
from typing import Dict, List, Any
from pathlib import Path

class CustomQualityMetrics:
    """Calculate custom quality metrics."""
    
    def __init__(self, target_path: str):
        self.target_path = Path(target_path)
    
    def calculate_complexity_metrics(self) -> Dict[str, float]:
        """Calculate cyclomatic complexity."""
        total_complexity = 0
        function_count = 0
        
        for py_file in self.target_path.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = self._calculate_node_complexity(node)
                        total_complexity += complexity
                        function_count += 1
            except Exception:
                continue
        
        avg_complexity = total_complexity / function_count if function_count > 0 else 0
        
        return {
            'total_complexity': total_complexity,
            'function_count': function_count,
            'average_complexity': avg_complexity,
            'complexity_score': max(0, 100 - (avg_complexity * 5))  # Penalize high complexity
        }
    
    def _calculate_node_complexity(self, node: ast.Ast) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def calculate_documentation_coverage(self) -> Dict[str, float]:
        """Calculate documentation coverage."""
        documented_functions = 0
        total_functions = 0
        
        for py_file in self.target_path.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)):
                            documented_functions += 1
            except Exception:
                continue
        
        coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            'documented_functions': documented_functions,
            'total_functions': total_functions,
            'documentation_coverage': coverage,
            'documentation_score': coverage
        }
    
    def calculate_security_score(self) -> Dict[str, float]:
        """Calculate basic security score."""
        security_issues = 0
        total_files = 0
        
        security_patterns = [
            'eval(',
            'exec(',
            'subprocess.call(',
            'os.system(',
            'shell=True'
        ]
        
        for py_file in self.target_path.rglob('*.py'):
            total_files += 1
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                for pattern in security_patterns:
                    if pattern in content:
                        security_issues += 1
            except Exception:
                continue
        
        security_score = max(0, 100 - (security_issues * 10))  # Deduct 10 points per issue
        
        return {
            'security_issues': security_issues,
            'total_files': total_files,
            'security_score': security_score
        }
    
    def generate_custom_metrics_report(self) -> Dict[str, Any]:
        """Generate comprehensive custom metrics report."""
        complexity_metrics = self.calculate_complexity_metrics()
        documentation_metrics = self.calculate_documentation_coverage()
        security_metrics = self.calculate_security_score()
        
        # Calculate overall custom quality score
        overall_score = (
            complexity_metrics['complexity_score'] * 0.4 +
            documentation_metrics['documentation_score'] * 0.3 +
            security_metrics['security_score'] * 0.3
        )
        
        return {
            'custom_metrics': {
                'complexity': complexity_metrics,
                'documentation': documentation_metrics,
                'security': security_metrics,
                'overall_custom_score': overall_score
            },
            'recommendations': self._generate_custom_recommendations(
                complexity_metrics, documentation_metrics, security_metrics
            )
        }
    
    def _generate_custom_recommendations(self, complexity: Dict, 
                                       documentation: Dict, 
                                       security: Dict) -> List[str]:
        """Generate recommendations for custom metrics."""
        recommendations = []
        
        if complexity['average_complexity'] > 10:
            recommendations.append(
                f"Reduce average function complexity from {complexity['average_complexity']:.1f} to < 10"
            )
        
        if documentation['documentation_coverage'] < 90:
            recommendations.append(
                f"Improve documentation coverage from {documentation['documentation_coverage']:.1f}% to 90%+"
            )
        
        if security['security_issues'] > 0:
            recommendations.append(
                f"Address {security['security_issues']} potential security issues"
            )
        
        return recommendations

# Usage
metrics_calculator = CustomQualityMetrics('src/')
custom_report = metrics_calculator.generate_custom_metrics_report()
print(json.dumps(custom_report, indent=2))
```

### Multi-Environment Configuration

#### Environment-Specific Configurations

```json
{
    "environments": {
        "development": {
            "base_config": "test_framework_config.json",
            "overrides": {
                "quality_gates": {
                    "monolithic_modules": {"threshold": 2, "severity": "major"},
                    "naming_conventions": {"threshold": 90.0, "severity": "minor"},
                    "test_execution": {"threshold": 85.0, "severity": "major"}
                },
                "performance": {
                    "max_total_time": 1800,
                    "memory_limit_mb": 4096
                }
            }
        },
        "staging": {
            "base_config": "test_framework_config.json",
            "overrides": {
                "quality_gates": {
                    "monolithic_modules": {"threshold": 1, "severity": "major"},
                    "naming_conventions": {"threshold": 93.0, "severity": "major"},
                    "test_execution": {"threshold": 92.0, "severity": "major"}
                },
                "performance": {
                    "max_total_time": 1200,
                    "memory_limit_mb": 3072
                }
            }
        },
        "production": {
            "base_config": "test_framework_config.json",
            "overrides": {
                "quality_gates": {
                    "monolithic_modules": {"threshold": 0, "severity": "critical"},
                    "naming_conventions": {"threshold": 98.0, "severity": "critical"},
                    "test_execution": {"threshold": 98.0, "severity": "critical"},
                    "code_quality": {"threshold": 95.0, "severity": "critical"}
                },
                "performance": {
                    "max_total_time": 900,
                    "memory_limit_mb": 2048
                }
            }
        }
    }
}
```

#### Environment-Aware Execution

```python
# environment_aware_execution.py
import os
import json
from typing import Dict, Any
from pathlib import Path

class EnvironmentAwareExecution:
    """Environment-aware comprehensive test execution."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('CI_ENVIRONMENT', 'development')
        self.config = self._load_environment_config()
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration for current environment."""
        # Load base configuration
        base_config_path = Path('test_framework_config.json')
        if base_config_path.exists():
            with open(base_config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Load environment-specific overrides
        env_config_path = Path(f'configs/{self.environment}_config.json')
        if env_config_path.exists():
            with open(env_config_path, 'r') as f:
                env_config = json.load(f)
                self._deep_merge(config, env_config)
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge override configuration into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def run_environment_specific_tests(self) -> Dict[str, Any]:
        """Run tests with environment-specific configuration."""
        # Save environment-specific config
        env_config_path = Path(f'test_framework_config_{self.environment}.json')
        with open(env_config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Run comprehensive tests with environment config
        cmd = [
            'python', 'comprehensive_test_suite.py',
            '--config', str(env_config_path),
            '--output', f'reports/comprehensive_report_{self.environment}',
            '--parallel'
        ]
        
        if self.environment == 'production':
            cmd.extend(['--fail-fast', '--max-workers', '2'])
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'environment': self.environment,
            'config': self.config,
            'execution_result': {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        }

# Usage
executor = EnvironmentAwareExecution(os.getenv('CI_ENVIRONMENT', 'development'))
results = executor.run_environment_specific_tests()
```

### Integration with External Systems

#### Database Integration

```python
# database_integration.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List
from contextlib import contextmanager

class QualityMetricsDatabase:
    """Store and retrieve quality metrics from database."""
    
    def __init__(self, db_path: str = 'quality_metrics.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quality_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    branch TEXT,
                    commit_hash TEXT,
                    overall_status TEXT NOT NULL,
                    overall_compliance REAL NOT NULL,
                    execution_time REAL NOT NULL,
                    json_report TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS gate_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    gate_name TEXT NOT NULL,
                    passed BOOLEAN NOT NULL,
                    actual_value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES quality_runs (id)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def store_test_results(self, results: Dict[str, Any], 
                          environment: str, branch: str = None, 
                          commit_hash: str = None) -> int:
        """Store comprehensive test results."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert main run record
            cursor.execute('''
                INSERT INTO quality_runs (
                    run_timestamp, environment, branch, commit_hash,
                    overall_status, overall_compliance, execution_time, json_report
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                environment,
                branch,
                commit_hash,
                results['quality_assessment']['overall_status'],
                results['execution_summary']['overall_compliance'],
                results['execution_summary']['total_execution_time'],
                json.dumps(results)
            ))
            
            run_id = cursor.lastrowid
            
            # Insert gate results
            for tool_result in results.get('tool_results', []):
                cursor.execute('''
                    INSERT INTO gate_results (
                        run_id, gate_name, passed, actual_value, threshold, severity
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    run_id,
                    tool_result['tool_name'],
                    tool_result['success'],
                    tool_result.get('metrics', {}).get('compliance_rate', 0.0),
                    95.0,  # Default threshold
                    'major'  # Default severity
                ))
            
            conn.commit()
            return run_id
    
    def get_quality_trends(self, environment: str, days: int = 30) -> Dict[str, Any]:
        """Get quality trends for specified environment."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get overall trends
            cursor.execute('''
                SELECT 
                    DATE(run_timestamp) as date,
                    AVG(overall_compliance) as avg_compliance,
                    AVG(execution_time) as avg_execution_time,
                    COUNT(*) as run_count
                FROM quality_runs
                WHERE environment = ? 
                  AND run_timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(run_timestamp)
                ORDER BY date
            '''.format(days), (environment,))
            
            trends = cursor.fetchall()
            
            # Get gate-specific trends
            cursor.execute('''
                SELECT 
                    gate_name,
                    AVG(CASE WHEN passed THEN 100.0 ELSE 0.0 END) as pass_rate,
 AVG(actual_value) as avg_actual_value
                FROM gate_results gr
                JOIN quality_runs qr ON gr.run_id = qr.id
                WHERE qr.environment = ?
                  AND qr.run_timestamp >= datetime('now', '-{} days')
                GROUP BY gate_name
            '''.format(days), (environment,))
            
            gate_trends = cursor.fetchall()
            
            return {
                'environment': environment,
                'period_days': days,
                'overall_trends': [
                    {
                        'date': row[0],
                        'avg_compliance': row[1],
                        'avg_execution_time': row[2],
                        'run_count': row[3]
                    }
                    for row in trends
                ],
                'gate_trends': [
                    {
                        'gate_name': row[0],
                        'pass_rate': row[1],
                        'avg_actual_value': row[2]
                    }
                    for row in gate_trends
                ]
            }

# Usage
db = QualityMetricsDatabase()

# Store results
results = {'quality_assessment': {'overall_status': 'PASS'}, 
          'execution_summary': {'overall_compliance': 95.5, 'total_execution_time': 120.0}}
run_id = db.store_test_results(results, 'production', 'main', 'abc123')

# Get trends
trends = db.get_quality_trends('production', 30)
```

---

## Monitoring and Alerts

### Metrics Collection

#### Prometheus Integration

```python
# prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import json
from typing import Dict, Any

# Define metrics
quality_gates_total = Counter('quality_gates_total', 'Total quality gates evaluated', ['gate_name', 'status'])
quality_gates_duration = Histogram('quality_gates_duration_seconds', 'Time spent evaluating quality gates')
overall_compliance = Gauge('overall_compliance_percent', 'Overall compliance percentage')
test_execution_time = Histogram('test_execution_seconds', 'Test execution time')
memory_usage = Gauge('memory_usage_mb', 'Memory usage in MB')

class PrometheusMetricsCollector:
    """Collect and expose metrics to Prometheus."""
    
    def __init__(self, port: int = 8000):
        self.port = port
    
    def start_server(self):
        """Start Prometheus metrics server."""
        start_http_server(self.port)
        print(f"Prometheus metrics server started on port {self.port}")
    
    def collect_test_results(self, results: Dict[str, Any]):
        """Collect metrics from test results."""
        # Overall compliance
        compliance = results['execution_summary']['overall_compliance']
        overall_compliance.set(compliance)
        
        # Execution time
        exec_time = results['execution_summary']['total_execution_time']
        test_execution_time.observe(exec_time)
        
        # Quality gates
        for tool_result in results['tool_results']:
            gate_name = tool_result['tool_name']
            status = 'passed' if tool_result['success'] else 'failed'
            
            quality_gates_total.labels(gate_name=gate_name, status=status).inc()
        
        # Memory usage (if available)
        if 'memory_usage' in results.get('execution_summary', {}):
            memory = results['execution_summary']['memory_usage']
            memory_usage.set(memory)
    
    def collect_custom_metrics(self, custom_metrics: Dict[str, Any]):
        """Collect custom quality metrics."""
        # This would integrate with your custom metrics
        pass

# Usage
collector = PrometheusMetricsCollector()
collector.start_server()

# In your test execution loop
results = {'execution_summary': {'overall_compliance': 95.5, 'total_execution_time': 120.0},
          'tool_results': [{'tool_name': 'monolithic_detector', 'success': True}]}
collector.collect_test_results(results)
```

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Comprehensive Testing Framework Metrics",
    "panels": [
      {
        "title": "Overall Compliance Score",
        "type": "stat",
        "targets": [
          {
            "expr": "overall_compliance_percent",
            "legendFormat": "Compliance %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "green", "value": 90}
              ]
            }
          }
        }
      },
      {
        "title": "Quality Gates Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(quality_gates_total) by (status)",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Test Execution Time",
        "type": "graph",
        "targets": [
          {
            "expr": "test_execution_seconds",
            "legendFormat": "Execution Time"
          }
        ]
      }
    ]
  }
}
```

### Alerting Configuration

#### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@company.com'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'

- name: 'critical-alerts'
  email_configs:
  - to: 'dev-team@company.com'
    subject: 'CRITICAL: Quality Gates Failed'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Severity: {{ .Labels.severity }}
      {{ end }}
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK'
    channel: '#dev-alerts'
    title: 'Critical Quality Gate Failure'
    text: 'Quality gates have failed. Immediate attention required.'

- name: 'warning-alerts'
  email_configs:
  - to: 'team@company.com'
    subject: 'WARNING: Quality Metrics Degraded'
    body: |
      Quality metrics have degraded but haven't failed yet.
      Please review the dashboard for details.
```

#### Prometheus Alert Rules

```yaml
# alert_rules.yml
groups:
- name: quality_gates
  rules:
  - alert: QualityGateFailed
    expr: quality_gates_total{status="failed"} > 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Quality gate {{ $labels.gate_name }} failed"
      description: "Quality gate {{ $labels.gate_name }} has failed for {{ $value }} times"
  
  - alert: ComplianceScoreLow
    expr: overall_compliance_percent < 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Overall compliance score is low"
      description: "Compliance score is {{ $value }}%, below 90% threshold"
  
  - alert: TestExecutionTimeHigh
    expr: test_execution_seconds > 1800
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Test execution time is high"
      description: "Test execution took {{ $value }} seconds, above 30 minute threshold"
  
  - alert: MemoryUsageHigh
    expr: memory_usage_mb > 2048
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Memory usage is high"
      description: "Memory usage is {{ $value }}MB, above 2GB threshold"
```

### Notification Systems

#### Slack Integration

```python
# slack_notifications.py
import requests
import json
from typing import Dict, Any

class SlackNotifier:
    """Send notifications to Slack."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_quality_gate_failure(self, results: Dict[str, Any]):
        """Send notification about quality gate failure."""
        failed_gates = [
            tool for tool in results['tool_results'] 
            if not tool['success']
        ]
        
        message = {
            "text": "🚨 Quality Gates Failed",
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {
                            "title": "Failed Gates",
                            "value": "\n".join([f"• {gate['tool_name']}" for gate in failed_gates]),
                            "short": False
                        },
                        {
                            "title": "Overall Status",
                            "value": results['quality_assessment']['overall_status'],
                            "short": True
                        },
                        {
                            "title": "Compliance",
                            "value": f"{results['execution_summary']['overall_compliance']:.1f}%",
                            "short": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Report",
                            "url": f"{self._get_build_url()}/reports"
                        }
                    ]
                }
            ]
        }
        
        self._send_message(message)
    
    def send_quality_gate_success(self, results: Dict[str, Any]):
        """Send notification about quality gate success."""
        message = {
            "text": "✅ Quality Gates Passed",
            "attachments": [
                {
                    "color": "good",
                    "fields": [
                        {
                            "title": "Overall Status",
                            "value": "PASS",
                            "short": True
                        },
                        {
                            "title": "Compliance",
                            "value": f"{results['execution_summary']['overall_compliance']:.1f}%",
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        self._send_message(message)
    
    def _send_message(self, message: Dict[str, Any]):
        """Send message to Slack."""
        response = requests.post(
            self.webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
    
    def _get_build_url(self) -> str:
        """Get current build URL (customize for your CI/CD system)."""
        return os.getenv('BUILD_URL', 'http://localhost')

# Usage
slack_notifier = SlackNotifier('YOUR_SLACK_WEBHOOK_URL')

if quality_assessment['overall_status'] == 'FAIL':
    slack_notifier.send_quality_gate_failure(results)
else:
    slack_notifier.send_quality_gate_success(results)
```

#### Teams Integration

```python
# teams_notifications.py
import requests
import json
from typing import Dict, Any

class TeamsNotifier:
    """Send notifications to Microsoft Teams."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_quality_report(self, results: Dict[str, Any]):
        """Send comprehensive quality report to Teams."""
        if results['quality_assessment']['overall_status'] == 'FAIL':
            self._send_failure_notification(results)
        else:
            self._send_success_notification(results)
    
    def _send_failure_notification(self, results: Dict[str, Any]):
        """Send failure notification."""
        failed_gates = [
            tool for tool in results['tool_results'] 
            if not tool['success']
        ]
        
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": "Quality Gates Failed",
            "themeColor": "FF0000",
            "sections": [
                {
                    "activityTitle": "🚨 Quality Gates Failed",
                    "activitySubtitle": "Build cannot proceed",
                    "facts": [
                        {"name": "Failed Gates", "value": str(len(failed_gates))},
                        {"name": "Compliance", "value": f"{results['execution_summary']['overall_compliance']:.1f}%"},
                        {"name": "Execution Time", "value": f"{results['execution_summary']['total_execution_time']:.1f}s"}
                    ],
                    "markdown": True
                },
                {
                    "title": "Failed Quality Gates:",
                    "text": "\n".join([f"❌ {gate['tool_name']}" for gate in failed_gates])
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Detailed Report",
                    "targets": [
                        {"os": "default", "uri": f"{self._get_build_url()}/reports"}
                    ]
                }
            ]
        }
        
        self._send_card(card)
    
    def _send_success_notification(self, results: Dict[str, Any]):
        """Send success notification."""
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": "Quality Gates Passed",
            "themeColor": "00FF00",
            "sections": [
                {
                    "activityTitle": "✅ Quality Gates Passed",
                    "activitySubtitle": "Build ready for deployment",
                    "facts": [
                        {"name": "Compliance", "value": f"{results['execution_summary']['overall_compliance']:.1f}%"},
                        {"name": "Execution Time", "value": f"{results['execution_summary']['total_execution_time']:.1f}s"},
                        {"name": "Tools Passed", "value": str(results['execution_summary']['successful_tools'])}
                    ],
                    "markdown": True
                }
            ]
        }
        
        self._send_card(card)
    
    def _send_card(self, card: Dict[str, Any]):
        """Send card to Teams."""
        response = requests.post(
            self.webhook_url,
            json=card,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
    
    def _get_build_url(self) -> str:
        """Get current build URL."""
        return os.getenv('BUILD_URL', 'http://localhost')

# Usage
teams_notifier = TeamsNotifier('YOUR_TEAMS_WEBHOOK_URL')
teams_notifier.send_quality_report(results)
```

---

## Conclusion

This comprehensive CI/CD integration guide provides everything needed to implement the Comprehensive Testing Framework across popular CI/CD platforms. The framework ensures consistent quality enforcement, automated testing, and comprehensive reporting throughout the development lifecycle.

### Key Benefits

- **Automated Quality Enforcement**: Quality gates prevent deployment of substandard code
- **Multi-Platform Support**: Works with GitHub Actions, GitLab CI, Jenkins, and Azure DevOps
- **Comprehensive Reporting**: Detailed reports and metrics for continuous improvement
- **Performance Monitoring**: Memory and execution time tracking with alerting
- **Integration Ready**: Easy integration with existing development workflows

### Next Steps

1. **Configure your preferred CI/CD platform** using the provided examples
2. **Customize quality gates** to match your project's requirements
3. **Set up monitoring and alerting** for proactive quality management
4. **Train your development team** on the new CI/CD processes
5. **Continuously improve** based on metrics and feedback

For additional support and advanced configurations, refer to the project documentation or contact the development team.

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-31  
**Maintained By**: Development Team  
**Review Schedule**: Monthly