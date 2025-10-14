# 3D-MM Application Packaging Documentation

This document describes the packaging and distribution process for the 3D-MM (3D Model Manager) application.

## Overview

The 3D-MM application uses a comprehensive packaging system that creates:
- A standalone executable using PyInstaller
- A professional Windows installer using Inno Setup
- Automatic file associations for supported 3D formats
- Settings migration for seamless updates

## Build System Components

### 1. PyInstaller Configuration (`pyinstaller.spec`)

The PyInstaller configuration file defines how the application is packaged into a standalone executable.

**Key Features:**
- Includes all necessary dependencies (PySide5, PyQt3D, etc.)
- Bundles application resources
- Optimizes for size with UPX compression
- Includes version information

**Usage:**
```bash
pyinstaller pyinstaller.spec
```

### 2. Inno Setup Script (`installer/inno_setup.iss`)

The Inno Setup script creates a professional Windows installer with advanced features.

**Key Features:**
- Professional installation wizard
- File association registration (.stl, .obj, .3mf, .step/.stp)
- Desktop and Start Menu shortcuts
- Settings migration for updates
- Uninstall support with user data preservation

**Usage:**
```bash
iscc installer/inno_setup.iss
```

### 3. Automated Build Script (`build.py`)

The Python build script automates the entire packaging process with error handling and reporting.

**Features:**
- Dependency checking
- Automated testing integration
- Build report generation
- Flexible command-line options

**Usage:**
```bash
python build.py [options]
```

**Options:**
- `--no-tests`: Skip running tests
- `--no-installer`: Skip creating installer
- `--clean-only`: Only clean build directories
- `--config <file>`: Use custom configuration

### 4. Windows Batch File (`installer/build.bat`)

The batch file provides an easy way to build on Windows systems without additional setup.

**Features:**
- Automatic dependency installation
- Python version checking
- Simplified build process
- Detailed error reporting

**Usage:**
```cmd
installer\build.bat [options]
```

## Build Process

### Prerequisites

**Required Tools:**
- Python 3.8+ (64-bit)
- PyInstaller
- Inno Setup (for installer creation)

**Python Dependencies:**
```
PySide5>=5.15.0
PyQt3D>=5.15.0
PyInstaller>=5.0.0
Pillow (for icon creation)
```

**Optional Dependencies:**
```
vtk>=9.2.0
numpy>=1.24.0
lxml>=4.6.0
```

### Build Steps

1. **Prepare Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Automated Build**
   ```bash
   python build.py
   ```

   Or on Windows:
   ```cmd
   installer\build.bat
   ```

3. **Verify Output**
   - Check `dist/` directory for generated files
   - Review `build_report.json` for build details

### Build Outputs

The build process generates the following files in the `dist/` directory:

- `3D-MM.exe` - Standalone executable
- `3D-MM-Setup-1.0.0.exe` - Windows installer
- `build_report.json` - Build summary and statistics
- `_internal/` - Required dependencies (for executable)

## File Associations

The installer registers the following file associations:

| Extension | Description | Application Name |
|-----------|-------------|------------------|
| .stl | Stereolithography | 3D-MM STL File |
| .obj | Wavefront Object | 3D-MM OBJ File |
| .3mf | 3D Manufacturing Format | 3D-MM 3MF File |
| .step | Standard for Exchange of Product Data | 3D-MM STEP File |
| .stp | STEP format alias | 3D-MM STEP File |

## Settings Migration

The application includes automatic settings migration to preserve user data during updates.

### Migration Process

1. **Detection**: Application checks for previous installation
2. **Backup**: Current settings are backed up
3. **Migration**: Settings and data are migrated
4. **Cleanup**: Old data is optionally cleaned up

### Migrated Components

- Application settings (`settings.json`)
- User database (`3dmm.db`)
- Model library files
- User preferences and customizations
- Recent files list

### Migration Triggers

- Version change detection
- Missing settings in new installation
- Manual migration request

## Installer Assets

The installer requires the following assets in `installer/assets/`:

### Required Files

- `license.txt` - End User License Agreement
- `readme.txt` - Installation guide and system requirements

### Optional Files

- `app_icon.ico` - Application icon (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
- `setup_icon.ico` - Installer icon
- `wizard_image.bmp` - Welcome screen image (164x314 pixels)
- `small_image.bmp` - Side panel image (55x55 pixels)

## Quality Assurance

### Testing Procedures

1. **Installation Testing**
   - Test on clean Windows system
   - Verify file associations work
   - Test shortcut creation
   - Verify uninstallation process

2. **Application Testing**
   - Launch from installed location
   - Test all supported file formats
   - Verify settings persistence
   - Test migration scenarios

3. **Performance Testing**
   - Measure startup time
   - Test memory usage
   - Verify load times for large models

### Build Verification

After each build, verify:

- [ ] Executable launches without errors
- [ ] All dependencies are bundled
- [ ] File associations work correctly
- [ ] Installer completes successfully
- [ ] Uninstaller removes all components
- [ ] Settings migration preserves data

## Troubleshooting

### Common Issues

**PyInstaller Build Fails**
- Check Python version compatibility
- Verify all dependencies are installed
- Check for missing hidden imports in spec file

**Installer Creation Fails**
- Verify Inno Setup is installed and in PATH
- Check installer script syntax
- Verify all required assets exist

**Application Won't Start**
- Check graphics drivers
- Verify OpenGL/DirectX support
- Run as administrator for testing

**File Associations Don't Work**
- Repair installation
- Manually associate files with executable
- Check registry permissions

### Debug Mode

For debugging, build without UPX compression:
```bash
pyinstaller pyinstaller.spec --noconfirm --clean --noupx
```

### Verbose Logging

Enable verbose logging during build:
```bash
python build.py --verbose
```

## Release Process

1. **Preparation**
   - Update version numbers
   - Create release notes
   - Test on target systems

2. **Build**
   - Clean previous builds
   - Run full build with tests
   - Verify outputs

3. **Distribution**
   - Upload installer to distribution platform
   - Create documentation
   - Announce release

4. **Post-Release**
   - Monitor for issues
   - Collect user feedback
   - Prepare patches if needed

## Customization

### Modifying Build Configuration

Edit `build.py` to customize:
- Application metadata
- Build options
- Dependency requirements
- Output locations

### Customizing Installer

Edit `installer/inno_setup.iss` to customize:
- Installation paths
- Registry entries
- User interface
- Components and features

### Adding New File Formats

1. Update file associations in `inno_setup.iss`
2. Add format support to parsers
3. Update documentation
4. Test new formats

## Security Considerations

- Code signing for executable and installer
- Secure distribution channels
- Dependency vulnerability scanning
- User data protection during migration

## Performance Optimization

- Optimize PyInstaller spec for smaller executable
- Use UPX compression for size reduction
- Minimize dependency footprint
- Optimize resource bundling

## Future Enhancements

- Auto-update mechanism
- Portable version creation
- Digital signature integration
- Silent installation support
- Custom theme support