@echo off
REM Quick Test Runner Script for Candy-Cadence (Windows)
REM Runs all tests with various options

setlocal enabledelayedexpansion

REM Get project root
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:menu
cls
echo ========================================
echo Candy-Cadence Test Runner
echo ========================================
echo.
echo 1) Run all tests (basic)
echo 2) Run all tests (verbose)
echo 3) Run all tests (stop on first failure)
echo 4) Run all tests (detailed with reports)
echo 5) Generate JSON report
echo 6) Generate HTML report
echo 7) Generate both reports
echo 8) Exit
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto run_basic
if "%choice%"=="2" goto run_verbose
if "%choice%"=="3" goto run_failfast
if "%choice%"=="4" goto run_detailed
if "%choice%"=="5" goto run_json
if "%choice%"=="6" goto run_html
if "%choice%"=="7" goto run_both
if "%choice%"=="8" goto exit_script
echo Invalid option
timeout /t 2 /nobreak
goto menu

:run_basic
cls
echo ========================================
echo Running Basic Tests
echo ========================================
python run_all_tests.py
pause
goto menu

:run_verbose
cls
echo ========================================
echo Running Tests (Verbose)
echo ========================================
python run_all_tests.py --verbose
pause
goto menu

:run_failfast
cls
echo ========================================
echo Running Tests (Fail Fast)
echo ========================================
python run_all_tests.py --failfast
pause
goto menu

:run_detailed
cls
echo ========================================
echo Running Detailed Tests
echo ========================================
python run_all_tests_detailed.py
pause
goto menu

:run_json
cls
echo ========================================
echo Generating JSON Report
echo ========================================
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set REPORT_FILE=test_report_!mydate!_!mytime!.json
python run_all_tests_detailed.py --json !REPORT_FILE!
echo.
echo Report saved to: !REPORT_FILE!
pause
goto menu

:run_html
cls
echo ========================================
echo Generating HTML Report
echo ========================================
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set REPORT_FILE=test_report_!mydate!_!mytime!.html
python run_all_tests_detailed.py --html !REPORT_FILE!
echo.
echo Report saved to: !REPORT_FILE!
start !REPORT_FILE!
pause
goto menu

:run_both
cls
echo ========================================
echo Generating Both Reports
echo ========================================
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set JSON_FILE=test_report_!mydate!_!mytime!.json
set HTML_FILE=test_report_!mydate!_!mytime!.html
python run_all_tests_detailed.py --json !JSON_FILE! --html !HTML_FILE!
echo.
echo JSON report saved to: !JSON_FILE!
echo HTML report saved to: !HTML_FILE!
start !HTML_FILE!
pause
goto menu

:exit_script
exit /b 0

