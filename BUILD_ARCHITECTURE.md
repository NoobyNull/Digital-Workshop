# Digital Workshop - Build Architecture & Development Guidelines

## Core Constitution (v1.1.0)

The application is governed by the **Digital Workshop Constitution** (`.specify/memory/constitution.md`), which defines five core principles:

### I. Performance Mandate
- **UI Responsiveness**: Must remain responsive during file loading and model interaction
- **Load Time Targets**: Files under 100MB should load in < 5 seconds
- **Memory Usage**: Must remain under 2GB during typical operations
- **Frame Rate**: Minimum 30 FPS during model interaction

### II. Modular Architecture
- Single responsibility principle for each module
- Clean, documented interfaces between modules
- Parser modules operate independently (STL, OBJ, STEP, 3MF)
- GUI components decoupled from business logic via service layers
- Database operations through facade patterns
- Theme system as pluggable service
- All modules independently testable
- Dependencies flow one direction (no circular references)

### III. Quality Assurance
- Basic logging at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Unit tests for parsers, integration tests for workflows
- Documentation for public functions and key modules
- Code passes basic linting checks
- Useful error messages and logging for debugging

### IV. User Sovereignty
- **Offline-First**: No remote execution or data transmission
- **Local Data**: All data stored locally in SQLite database
- **No Telemetry**: No analytics, tracking, or external communication
- **Privacy by Design**: No user behavior tracking or personal data collection
- **User Control**: Complete control over application behavior, themes, and data

### V. Windows Integration
- Designed for modern Windows systems
- Adheres to standard desktop conventions
- Local file system access follows Windows conventions

---

## Build & Release Pipeline

### Build Workflow (`.github/workflows/build.yml`)
Triggered on GitHub release publication:
1. **Setup**: Python 3.10, pip dependencies, PyInstaller
2. **Build**: `pyinstaller --onefile --name "Digital Workshop" src/main.py`
3. **Installer**: NSIS-based installer creation
4. **Release**: Upload executable to GitHub release

### Release Workflow (`.github/workflows/release.yml`)
Manual workflow with version bumping:
1. **Version Management**: Semantic versioning (MAJOR.MINOR.PATCH)
2. **Version Updates**: Updates `build.py` and `config/installer.nsi`
3. **Release Branch**: Creates `release/v*` branch
4. **Build**: Runs `python build.py --no-tests`
5. **Artifacts**: Generates executable and installer
6. **Release Notes**: Auto-generates from commit history
7. **Merge**: Merges to main, creates version tag, deletes release branch

### Key Build Files
- **`build.py`**: Main build script (contains version string)
- **`config/installer.nsi`**: NSIS installer configuration
- **`requirements.txt`**: Python dependencies
- **`src/main.py`**: Application entry point

---

## Development Workflow

### Taskmaster Integration (`.github/instructions/dev_workflow.instructions.md`)
- **Default Context**: Master task list for most work
- **Tagged Tasks**: Create separate contexts for features, experiments, team collaboration
- **Task Structure**: id, title, description, status, dependencies, priority, details, testStrategy, subtasks
- **Status Values**: pending, done, deferred (or custom)
- **MCP Server**: Preferred interaction method for AI agents
- **CLI Fallback**: `task-master` command for direct terminal use

### Task Management Patterns
1. **Simple Git Branching**: Create task tag matching branch name
2. **Team Collaboration**: Separate tags for each team member's work
3. **Experiments**: Sandboxed tags for risky refactors
4. **Large Features**: PRD-driven workflow with dedicated tags
5. **Version-Based**: Different approaches for MVP vs production tags

### Configuration
- **`.taskmaster/config.json`**: Main configuration (AI models, parameters, logging)
- **`.env` / `.vscode/mcp.json`**: API keys and sensitive data
- **`.taskmaster/state.json`**: Tagged system state tracking

---

## Performance & Quality Standards

### Performance Requirements (`.kilocode/rules/performance-requirements.md`)
**Load Times:**
- < 5 seconds for files under 100MB
- < 15 seconds for files 100-500MB
- < 30 seconds for files over 500MB

**Memory Management:**
- Maximum 2GB for typical usage
- Adaptive cache sizing based on available RAM
- No memory leaks during repeated operations

**Responsiveness:**
- UI remains responsive during loading
- Progress feedback for long operations
- Cancellation support
- Minimum 30 FPS during interaction

### Quality Standards (`.kilocode/rules/quality-standards.md`)
**Code Quality:**
- JSON logging for all modules
- Run operations 10-20 times to verify no memory leaks
- Unit tests for parsers, integration tests for workflows
- Performance benchmarking for load times

**Documentation:**
- Inline documentation for public functions
- Module-level docstrings
- Usage examples
- Troubleshooting guides

**Quality Gates:**
- All code must pass code review
- Memory usage stable during stress testing
- Performance targets verified
- Documentation complete and accurate

---

## VS Code Integration

### Settings (`.vscode/settings.json`)
- **Testing Framework**: pytest (enabled)
- **Test Directory**: `tests/`

### MCP Configuration (`.vscode/mcp.json`)
- **Server**: task-master-ai via npx
- **API Keys**: Anthropic, Perplexity, OpenAI, Google, xAI, OpenRouter, Mistral, Azure, Ollama

### Rule Structure (`.github/instructions/vscode_rules.instructions.md`)
- **Format**: Markdown with YAML frontmatter
- **Frontmatter**: description, globs, alwaysApply
- **Content**: Bold main points, sub-points with details, DO/DON'T examples
- **References**: Use `[filename](mdc:path)` for file references

---

## Governance & Amendments

**Constitution Compliance:**
- Constitution supersedes all other practices
- Amendments require written proposals with rationale and impact analysis
- Breaking changes require MAJOR version increments with 90-day deprecation warnings
- All PRs must verify constitution compliance
- Feature flags required for experimental implementations
- Atomic commits enforce single logical changes

**Versioning:**
- Semantic versioning: MAJOR.MINOR.PATCH
- Backwards compatibility guaranteed for MINOR and PATCH releases
- Breaking changes require MAJOR version increments

---

## Key Directories

- **`.specify/`**: Project specifications and memory
- **`.github/`**: Workflows, instructions, and CI/CD
- **`.vscode/`**: VS Code settings and MCP configuration
- **`.kilo/`**: Kilo AI assistant rules and workflows
- **`.kilocode/`**: Kilocode AI assistant rules and workflows
- **`src/`**: Application source code
- **`tests/`**: Test suite
- **`config/`**: Configuration files (installer, etc.)

---

## Summary

Digital Workshop is built on a **constitution-driven architecture** emphasizing:
- **Performance**: Responsive UI, fast loading, efficient memory usage
- **Modularity**: Independent, testable components with clean interfaces
- **Quality**: Comprehensive logging, testing, and documentation
- **User Sovereignty**: Offline-first, local data, no telemetry
- **Windows Integration**: Native desktop application conventions

Development follows **task-driven workflows** with semantic versioning and automated release pipelines.

