# Digital Workshop - Build System Guide

## Overview

This document describes the improved build system for Digital Workshop that uses sequential build numbers instead of versioning, generates automatic change logs, and keeps all artifacts permanently.

## 🚀 Quick Start

### For Windows Users (Easiest)
```bash
# Just double-click this file or run from command line
build.bat
```

### For Command Line Users
```bash
# Quick build (no tests)
python scripts/easy_build.py quick

# Full build (with tests)
python scripts/easy_build.py full

# Setup development environment
python scripts/easy_build.py setup

# Clean all artifacts
python scripts/easy_build.py clean

# Show build information
python scripts/easy_build.py info
```

## 🌐 GitHub Mirror Prep

The same tooling used in GitLab CI works inside GitHub Actions when mirrored:

1. **Cache Poetry/Pip artifacts:** Use `actions/setup-python` + `actions/cache` targeting `.venv` or `%LocalAppData%\pip\Cache`.
2. **Build step:** `python scripts/easy_build.py full`.
3. **Release packaging:**
   ```bash
   $env:DW_BUILD_NUMBER = $env:GITHUB_RUN_NUMBER
   python scripts/generate_changelog.py --build-number $env:DW_BUILD_NUMBER --output dist/changes-$env:DW_BUILD_NUMBER.txt
   Rename-Item "dist/Digital Workshop.exe" "Digital Workshop.$env:DW_BUILD_NUMBER.exe"
   git tag build-$env:DW_BUILD_NUMBER
   ```
4. **Upload artifacts:** publish the renamed EXE + `dist/changes-*.txt` + `build-info.txt`.

GitHub exposes `GITHUB_RUN_NUMBER`, which is monotonic per workflow; treating it as the build number keeps parity with GitLab’s `CI_PIPELINE_IID`.

## 📦 Build Number System

Instead of semantic versioning (v0.1.5), we now use sequential build numbers:

- **Format**: `Digital Workshop.23456.exe`
- **Source**: GitLab CI pipeline IID (auto-incrementing)
- **Benefits**: 
  - Clear build progression
  - No version conflicts
  - Easy to track changes
  - Simple for users to understand

### Build Number Examples
- `Digital Workshop.1.exe` - First build
- `Digital Workshop.23456.exe` - Build #23,456
- `Digital Workshop.23457.exe` - Next build

## 📋 Automatic Change Logs

Every build automatically generates a change log showing what was modified:

### Change Log Features
- **Categorized Changes**: Features, Bug Fixes, Documentation, Other
- **Git Integration**: Automatically pulls commits since last build
- **Build Tagging**: Each build creates a `build-XXXXX` tag
- **Formatted Output**: Human-readable with emojis and clear sections

### Change Log Location
- **File**: `dist/changes-XXXXX.txt`
- **Format**: 
  ```
  Changes for Build 23456
  ==================================================
  
  🚀 NEW FEATURES:
    • Add new 3D model import feature
    • Implement thumbnail generation
  
  🐛 BUG FIXES:
    • Fix memory leak in model loading
    • Correct UI layout issues
  
  📚 DOCUMENTATION:
    • Update installation guide
    • Add API documentation
  ```

## 🔧 GitLab CI/CD Improvements

### Key Changes Made
1. **Build Number Naming**
   - Changed from `Digital Workshop-release-XXXXX.exe` to `Digital Workshop.XXXXX.exe`
   - Uses `$CI_PIPELINE_IID` for sequential numbering

2. **Permanent Artifacts**
   - Changed `expire_in: 1 year` to `expire_in: never`
   - All builds kept permanently for traceability

3. **Automatic Change Logs**
   - Added Python script to generate detailed change logs
   - Integrates with git history between builds
   - Creates structured, readable output

4. **Build Metadata**
   - Generates `build-info.txt` with build details
   - Creates `release-XXXXX.json` with full build information
   - Includes commit SHA, branch, timestamp, and pipeline URL

5. **Build Tagging**
   - Automatically tags each build as `build-XXXXX`
   - Enables change tracking between builds
   - Provides git history anchors

### Pipeline Rules
- **Main Branch**: Automatic builds on every commit
- **Manual Triggers**: Can trigger builds from GitLab UI
- **Test Integration**: Optional test execution before build

## 📁 Build Artifacts

Every build generates these files in `dist/`:

### Core Files
- `Digital Workshop.XXXXX.exe` - Main executable
- `changes-XXXXX.txt` - Human-readable change log
- `build-info.txt` - Build metadata
- `release-XXXXX.json` - Detailed build information

### Source Code (for debugging)
- `src/` - Complete source code
- `requirements.txt` - Dependencies list

### Optional Files (if tests run)
- `junit.xml` - Test results

## 🛠️ Development Workflow

### Daily Development
```bash
# 1. Make changes
git add .
git commit -m "feat: add new feature"

# 2. Quick test build
python scripts/easy_build.py quick

# 3. Run tests locally
python -m pytest

# 4. Push changes
git push origin main
```

### Release Process
```bash
# 1. Ensure tests pass
python scripts/easy_build.py full

# 2. Push to main (triggers CI build)
git push origin main

# 3. Monitor build in GitLab CI/CD
# 4. Download artifacts from GitLab
```

## 📊 Build Information

### Checking Current Status
```bash
python scripts/easy_build.py info
```

Shows:
- Current build number
- Last commit information
- Build artifacts status
- Git branch and commit

### Build History
```bash
# List all build tags
git tag -l "build-*"

# Show changes between builds
git log build-23455..build-23456 --oneline
```

## 🔄 Migration from Versioning

### Old System
- Format: `Digital Workshop v0.1.5`
- Manual version increments
- Semantic versioning complexity

### New System
- Format: `Digital Workshop.23456.exe`
- Automatic build numbers
- Simple and clear progression

### Benefits of Change
1. **Simpler**: No semantic versioning to manage
2. **Automatic**: Build numbers increment automatically
3. **Traceable**: Every build has unique identifier
4. **Clear**: Users can easily identify newer builds

## 🚨 Troubleshooting

### Common Issues

**Build Fails**
```bash
# Check dependencies
python scripts/easy_build.py setup

# Clean and rebuild
python scripts/easy_build.py clean
python scripts/easy_build.py quick
```

**Missing Change Log**
```bash
# Check git tags
git tag -l "build-*"

# Manual changelog generation
python scripts/generate_changelog.py --build-number 23456 --output changes.txt
```

**CI/CD Issues**
- Check GitLab CI/CD pipeline logs
- Verify Windows runner is available
- Ensure all dependencies are in requirements files

## 🎯 Best Practices

### For Developers
1. **Commit Messages**: Use conventional format (`feat:`, `fix:`, `docs:`)
2. **Test Before Push**: Always run `python scripts/easy_build.py full`
3. **Clean Regularly**: Use `python scripts/easy_build.py clean` to free space
4. **Check Build Info**: Use `python scripts/easy_build.py info` to verify status

### For Releases
1. **Tag Builds**: Each CI build automatically tags `build-XXXXX`
2. **Keep Artifacts**: All builds preserved permanently
3. **Document Changes**: Automatic changelog generation
4. **Monitor Pipeline**: Check GitLab CI/CD for build status

## 📞 Support

For build system issues:
1. Check this document first
2. Review GitLab CI/CD pipeline logs
3. Examine build artifacts and change logs
4. Check git history and tags

---

**Last Updated**: November 16, 2025  
**System**: Build Number v2.0  
**Compatible**: GitLab CI/CD, Windows, Linux, macOS
### 🔒 Security Features

**Comprehensive Security Scanning:**
- **Dependency Vulnerability Scanning**: Safety checks for known vulnerabilities
- **Static Code Analysis**: Bandit for Python security issues
- **Semantic Analysis**: Semgrep for security patterns
- **Database Security**: Checks for hardcoded secrets in database files
- **Token Detection**: Scans for API keys, passwords, certificates
- **Permission Verification**: Ensures proper file permissions

**Security Reports Generated:**
- `safety-report.json` - Dependency vulnerability findings
- `bandit-report.json` - Static analysis security issues
- `semgrep-report.json` - Semantic analysis results
- All reports included in GitLab artifacts

**Security Configuration:**
- [`config/security.yaml`](config/security.yaml:1) - Comprehensive security settings
- Configurable severity levels and patterns
- Excludes test files from scanning
- Customizable ignore rules

---
