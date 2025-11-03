# Automated Builds with GitHub Actions

Digital Workshop uses GitHub Actions to automatically build and publish releases.

## Build Workflows

### 1. **Build and Release Workflow** (`build.yml`)
Automatically triggered when a release is published on GitHub.

**Trigger Events:**
- Release published on GitHub
- Manual trigger via `workflow_dispatch`

**What it does:**
- Checks out the code
- Sets up Python 3.12
- Installs dependencies from `requirements.txt`
- Installs Inno Setup for Windows installer creation
- Runs `python build.py --no-tests`
- Verifies the executable was created
- Uploads artifacts to the GitHub Release:
  - `Digital Workshop.exe` (main executable)
  - `build_report.json` (build metadata)

**Artifacts Location:**
- GitHub Release page: https://github.com/NoobyNull/Digital-Workshop/releases

---

### 2. **Release Workflow** (`release.yml`)
Manual workflow for creating versioned releases with automatic version bumping.

**How to Use:**
1. Go to GitHub Actions tab
2. Select "Release - Manual Release Workflow"
3. Click "Run workflow"
4. Choose version bump type:
   - **patch**: 0.1.5 → 0.1.6 (bug fixes)
   - **minor**: 0.1.5 → 0.2.0 (new features)
   - **major**: 0.1.5 → 1.0.0 (breaking changes)
5. (Optional) Add custom release notes
6. Click "Run workflow"

**What it does:**
- Detects current version from `src/core/version_manager.py`
- Calculates new version based on bump type
- Updates all version files:
  - `src/core/version_manager.py`
  - `pyproject.toml`
  - `build.py`
  - `config/installer.iss`
- Creates release branch
- Builds the application
- Generates release notes from commit history
- Creates GitHub Release with tag
- Uploads artifacts
- Merges to main branch
- Cleans up release branch

---

## Quick Start

### Option 1: Manual Release (Recommended)
```bash
# Push your changes to develop branch
git push origin develop

# Go to GitHub Actions → Release Workflow → Run workflow
# Select version bump type and run
```

### Option 2: Create Release on GitHub
```bash
# After pushing to develop, create a release on GitHub
# The build.yml workflow will automatically:
# 1. Build the application
# 2. Upload artifacts to the release
```

### Option 3: Manual Build Trigger
```bash
# Go to GitHub Actions → Build and Release → Run workflow
# This will build without creating a release
```

---

## Version Files Updated Automatically

When using the Release workflow, these files are automatically updated:

1. **src/core/version_manager.py**
   ```python
   self._base_version = "0.1.5"
   ```

2. **pyproject.toml**
   ```toml
   version = "0.1.5"
   ```

3. **build.py**
   ```python
   "version": "0.1.5"
   ```

4. **config/installer.iss**
   ```iss
   #define MyAppVersion "0.1.5"
   ```

---

## Build Artifacts

After a successful build, the following artifacts are available:

- **Digital Workshop.exe** (~230 MB)
  - Standalone executable
  - No installation required
  - Can be run directly

- **build_report.json**
  - Build metadata
  - Timestamps
  - Build status
  - Artifact information

---

## Troubleshooting

### Build Fails
1. Check the workflow logs on GitHub Actions
2. Common issues:
   - Missing dependencies in `requirements.txt`
   - Python version mismatch
   - Inno Setup not installed

### Release Not Created
1. Ensure you're on the `develop` branch
2. Check that version files are properly formatted
3. Verify GitHub token has write permissions

### Artifacts Not Uploaded
1. Check that `dist/` directory exists
2. Verify file paths in workflow match actual files
3. Check GitHub token permissions

---

## Local Testing

To test the build locally before pushing:

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Run build
python build.py --no-tests

# Check artifacts
ls -la dist/
```

---

## Environment Variables

The workflows use these environment variables:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `NEW_VERSION`: Set during release workflow for version bumping

---

## Next Steps

1. **Push to develop**: `git push origin develop`
2. **Create Release**: Use GitHub Actions Release workflow
3. **Monitor Build**: Check GitHub Actions tab for progress
4. **Download Artifacts**: Get from GitHub Release page

For more information, see the workflow files:
- `.github/workflows/build.yml`
- `.github/workflows/release.yml`

