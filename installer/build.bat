@echo off
REM 3D-MM (3D Model Manager) - Windows Build Script
REM This script provides an easy way to build the 3D-MM application on Windows

setlocal enabledelayedexpansion

echo ========================================
echo 3D-MM (3D Model Manager) Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again
    pause
    exit /b 1
)

REM Display Python version
echo Python version:
python --version
echo.

REM Check if we're in the correct directory
if not exist "src\main.py" (
    echo ERROR: src\main.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Parse command line arguments
set RUN_TESTS=1
set CREATE_INSTALLER=1
set CLEAN_ONLY=0

:parse_args
if "%~1"=="" goto end_parse
if /i "%~1"=="--no-tests" (
    set RUN_TESTS=0
    shift
    goto parse_args
)
if /i "%~1"=="--no-installer" (
    set CREATE_INSTALLER=0
    shift
    goto parse_args
)
if /i "%~1"=="--clean-only" (
    set CLEAN_ONLY=1
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    goto show_help
)
echo Unknown argument: %~1
goto show_help

:end_parse

REM Show help if requested
if "%CLEAN_ONLY%"=="1" goto clean_only

REM Check if required packages are installed
echo Checking required packages...

python -c "import PySide5" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PySide5 not found. Installing...
    pip install PySide5
    if errorlevel 1 (
        echo ERROR: Failed to install PySide5
        pause
        exit /b 1
    )
)

python -c "import PyQt3D" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PyQt3D not found. Installing...
    pip install PyQt3D
    if errorlevel 1 (
        echo ERROR: Failed to install PyQt3D
        pause
        exit /b 1
    )
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PyInstaller not found. Installing...
    pip install PyInstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PIL (Pillow) not found. Installing for icon creation...
    pip install Pillow
)

REM Check for optional dependencies
python -c "import vtk" >nul 2>&1
if errorlevel 1 (
    echo INFO: VTK not found. Optional advanced 3D visualization will not be available.
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo INFO: NumPy not found. Optional geometry processing will not be available.
)

echo All required packages are available.
echo.

REM Run the Python build script
echo Starting build process...
echo.

if "%RUN_TESTS%"=="1" (
    if "%CREATE_INSTALLER%"=="1" (
        python build.py
    ) else (
        python build.py --no-installer
    )
) else (
    if "%CREATE_INSTALLER%"=="1" (
        python build.py --no-tests
    ) else (
        python build.py --no-tests --no-installer
    )
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo BUILD FAILED
    echo ========================================
    echo.
    echo Check the build log for details.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETED SUCCESSFULLY
echo ========================================
echo.

REM Check if executable was created
if exist "dist\3D-MM.exe" (
    echo Executable created: dist\3D-MM.exe
    
    REM Show file size
    for %%F in ("dist\3D-MM.exe") do echo Executable size: %%~zF bytes
    echo.
)

REM Check if installer was created
if exist "dist\3D-MM-Setup-1.0.0.exe" (
    echo Installer created: dist\3D-MM-Setup-1.0.0.exe
    
    REM Show file size
    for %%F in ("dist\3D-MM-Setup-1.0.0.exe") do echo Installer size: %%~zF bytes
    echo.
)

REM Check if build report was created
if exist "dist\build_report.json" (
    echo Build report created: dist\build_report.json
    echo.
)

echo Build artifacts are located in the dist\ directory.
echo.
echo To test the application, run: dist\3D-MM.exe
echo.

pause
exit /b 0

:clean_only
echo Cleaning build directories...
if exist "build" (
    rmdir /s /q build
    echo Removed: build\
)
if exist "dist" (
    rmdir /s /q dist
    echo Removed: dist\
)
echo.
echo Build directories cleaned successfully.
echo.
pause
exit /b 0

:show_help
echo.
echo 3D-MM Build Script
echo.
echo Usage: build.bat [options]
echo.
echo Options:
echo   --no-tests       Skip running tests
echo   --no-installer   Skip creating installer
echo   --clean-only     Only clean build directories
echo   --help           Show this help message
echo.
echo Examples:
echo   build.bat              Build with tests and installer
echo   build.bat --no-tests    Build without tests
echo   build.bat --clean-only  Clean build directories
echo.
pause
exit /b 0