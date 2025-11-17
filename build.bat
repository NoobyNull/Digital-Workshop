@echo off
REM Easy build script for Digital Workshop on Windows

echo Digital Workshop - Easy Build Helper
echo =====================================

:menu
echo.
echo 1. Quick Build (no tests)
echo 2. Full Build (with tests)
echo 3. Setup Development Environment
echo 4. Clean All Artifacts
echo 5. Show Build Info
echo 6. Exit
echo.
set /p choice=Choose an option (1-6): 

if "%choice%"=="1" goto quick
if "%choice%"=="2" goto full
if "%choice%"=="3" goto setup
if "%choice%"=="4" goto clean
if "%choice%"=="5" goto info
if "%choice%"=="6" goto end

echo Invalid choice, please try again.
goto menu

:quick
echo.
echo Starting Quick Build...
python scripts\easy_build.py quick
pause
goto end

:full
echo.
echo Starting Full Build...
python scripts\easy_build.py full
pause
goto end

:setup
echo.
echo Setting up Development Environment...
python scripts\easy_build.py setup
pause
goto end

:clean
echo.
echo Cleaning All Artifacts...
python scripts\easy_build.py clean
pause
goto end

:info
echo.
echo Showing Build Information...
python scripts\easy_build.py info
pause
goto end

:end
echo.
echo Done!