3D-MM (3D Model Manager) - Installation Guide

Thank you for choosing 3D-MM, the professional 3D model viewing and management application.

SYSTEM REQUIREMENTS
===================

Minimum Requirements:
- Operating System: Windows 7 SP1 (64-bit)
- Processor: Intel Core i3-3220 (Ivy Bridge) or equivalent
- Graphics: Intel HD Graphics 4000 or equivalent
- Memory: 4GB RAM
- Storage: 100MB free space

Recommended Requirements:
- Operating System: Windows 10/11 (64-bit)
- Processor: Intel Core i5-3470 or equivalent
- Graphics: NVIDIA GeForce GTX 1050 or equivalent
- Memory: 8GB RAM
- Storage: 500MB free space (SSD recommended)

Graphics API Support:
- OpenGL 3.3 Core Profile minimum
- DirectX 11.0 minimum (via ANGLE fallback)
- Software rasterizer fallback (limited performance)

INSTALLATION
============

1. Run the installer executable (3D-MM-Setup-1.0.0.exe)
2. Follow the on-screen instructions
3. Choose your preferred installation location
4. Select which shortcuts to create
5. Complete the installation process

The installer will automatically:
- Register file associations for supported 3D formats
- Create Start Menu shortcuts
- Create desktop shortcut (optional)
- Configure the application for first use

SUPPORTED FILE FORMATS
======================

3D-MM supports the following 3D model formats:
- STL (Stereolithography) - .stl
- OBJ (Wavefront Object) - .obj
- 3MF (3D Manufacturing Format) - .3mf
- STEP (Standard for the Exchange of Product Data) - .step, .stp

GETTING STARTED
===============

After installation, you can:
1. Launch 3D-MM from the Start Menu or desktop shortcut
2. Open 3D model files using File > Open or drag-and-drop
3. Browse your model library using the built-in library manager
4. Search models by name, format, or metadata
5. Edit model properties and metadata
6. Export models to different formats

TROUBLESHOOTING
===============

Common Issues:

1. Application won't start:
   - Ensure your graphics drivers are up to date
   - Try running as administrator
   - Check if .NET Framework 4.5+ is installed

2. Models don't display correctly:
   - Update your graphics drivers
   - Check if your GPU supports OpenGL 3.3+
   - Try disabling hardware acceleration in settings

3. Performance issues:
   - Close other applications to free up memory
   - Reduce model complexity or detail level
   - Ensure sufficient disk space for temporary files

4. File associations not working:
   - Repair the installation using the installer
   - Manually associate files with 3D-MM.exe

For more detailed troubleshooting, please refer to the documentation included with the application or visit our support website.

UNINSTALLATION
==============

To remove 3D-MM from your system:
1. Open "Programs and Features" in Windows Control Panel
2. Select "3D-MM" from the list
3. Click "Uninstall"
4. Follow the on-screen instructions

You will be asked whether to keep or remove your user data and settings. Choose "Keep" if you plan to reinstall 3D-MM in the future.

SUPPORT & UPDATES
=================

For the latest updates, documentation, and support:
- Website: https://3dmm.local
- Documentation: Included in the installation
- Updates: Check for updates from within the application

THIRD-PARTY LICENSES
===================

3D-MM uses the following open-source components:
- PySide5/Qt - LGPLv3
- PyQt3D - GPL v3
- SQLite - Public Domain
- VTK - BSD 3-Clause License
- NumPy - BSD 3-Clause License

Full license information is available in the documentation folder.

Thank you for using 3D-MM!