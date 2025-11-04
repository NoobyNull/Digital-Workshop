# Digital Workshop Release History

This document tracks all releases of the Digital Workshop application.

## Release Index

| Version | Release Date | Type | Key Changes |
|---------|--------------|------|-------------|
| [v0.1.5](#v015---2025-11-04) | 2025-11-04 | Quality & Analysis Milestone | Comprehensive code analysis and refactoring planning |
| v0.1.4 | 2025-10-31 | Maintenance | Root directory cleanup and organization |
| v0.1.3 | 2025-10-15 | Feature | Gemini AI integration for metadata generation |
| v0.1.2 | 2025-09-20 | Feature | Tab data persistence and project management |
| v0.1.1 | 2025-08-15 | Bugfix | Various stability improvements |
| v0.1.0 | 2025-07-01 | Initial Release | Core 3D model viewing and management |

---

## Release Details

### v0.1.5 - 2025-11-04
**Type:** Quality & Analysis Milestone

**Summary:** This release focuses on comprehensive code quality assessment, technical debt identification, and architectural improvement planning.

**Key Highlights:**
- 🔍 **Comprehensive Linting Analysis**: Analyzed 150+ files, identified 3,450+ improvement opportunities
- 📋 **God Class Refactoring Plan**: Detailed strategy for decomposing MainWindow and ModelLibrary
- 🔒 **Security Assessment Updates**: Revised for desktop application context
- 🎯 **Code Quality Baseline**: Established metrics and improvement roadmap

**Documentation:**
- [Full Release Notes](v0.1.5-release-notes.md)
- [Executive Summary](release-summary-v0.1.5.md)
- [Git Commands](v0.1.5-git-commands.md)

**Next Steps:** Implementation of identified improvements in v0.2.0

---

### v0.1.4 - 2025-10-31
**Type:** Maintenance Release

**Summary:** Major cleanup of root directory structure, improving project organization and developer experience.

**Key Changes:**
- Reduced root directory files from 100+ to 30 (70% reduction)
- Organized files into logical directories
- Preserved all functionality
- Improved project navigation

---

### v0.1.3 - 2025-10-15
**Type:** Feature Release

**Summary:** Integration of Google Gemini AI for automated metadata generation from 3D model previews.

**Key Features:**
- AI-powered description generation
- Multiple Gemini model support
- Secure API key management
- Seamless UI integration

---

### v0.1.2 - 2025-09-20
**Type:** Feature Release

**Summary:** Enhanced project management with tab data persistence and improved workflow management.

**Key Features:**
- Tab state preservation
- Project-based workflows
- Enhanced file management
- Improved user experience

---

### v0.1.1 - 2025-08-15
**Type:** Bugfix Release

**Summary:** Stability improvements and bug fixes based on initial user feedback.

**Key Fixes:**
- Memory leak in model loading
- UI responsiveness improvements
- File format compatibility fixes
- Error handling enhancements

---

### v0.1.0 - 2025-07-01
**Type:** Initial Release

**Summary:** First public release of Digital Workshop for 3D model management and CNC workflow.

**Core Features:**
- 3D model viewing (STL, OBJ, 3MF, etc.)
- Material application and preview
- Model library management
- Basic metadata editing
- Export capabilities
- Theme customization

---

## Version Numbering

Digital Workshop follows semantic versioning:
- **Major** (X.0.0): Breaking changes or major rewrites
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes and small improvements

## Release Process

1. Create release branch from develop
2. Update version in `pyproject.toml` and `src/core/version_manager.py`
3. Create release notes and summary
4. Merge to main and tag
5. Update this index file

## Support Policy

- Latest version: Full support
- Previous minor version: Security updates only
- Older versions: Community support

---

*For detailed release procedures, see [v0.1.5-git-commands.md](v0.1.5-git-commands.md)*