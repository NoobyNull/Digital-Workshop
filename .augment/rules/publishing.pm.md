---
type: "manual"
---

# Augment Rule Prompt: Code Sanitization, Linting, Packaging

**Objective:**  
Ensure all code contributions are clean, secure, consistent, and packaged for distribution across platforms.

---

## Code Quality & Structure
- Enforce **maximum file length**: no source file may exceed **500 lines of code** (excluding comments and docstrings).  
- All code must achieve a **linting score of 9.5/10 or higher** using the project’s configured linter.  
- Code must be **properly formatted** according to the project’s style guide (e.g., PEP8, Prettier, ESLint, etc.).  
- Remove unused imports, dead code, and redundant logic.  

---

## Security & Sanitization
- **Strip all API keys, secrets, tokens, or credentials** from source files, configs, and documentation.  
- Replace sensitive values with environment variables or placeholders.  
- Verify that **no files from the developer’s local system** (samples, temp files, IDE configs, OS artifacts) are included in the repo.  

---

## Repository Hygiene
- Root directory must be **clean and organized**:  
  - Only essential project files (source, configs, docs, build scripts).  
  - No stray binaries, caches, or editor-specific files.  
- Apply `.gitignore` rules to exclude system or build artifacts.  
- Ensure consistent naming conventions across directories and files.  

---

## Build & Distribution
- Automatically **bump version numbers** following semantic versioning (major.minor.patch).  
- Generate builds for distribution:  
  - **Standalone EXE** (Windows)  
  - **Installer package** (per OS type)  
  - **Zip Bundler with auto-install script**  
  - **Source code bundle** (clean, sanitized, ready for distribution)  
- Validate that each build artifact installs and runs correctly on its target OS.  

---

## Compliance Checks
- Run full lint/test suite before packaging.  
- Reject builds that fail **any** of the above rules.  
- Provide a summary report of:  
  - Linting score  
  - Sanitization results  
  - Build artifacts generated  
  - Directory cleanliness status