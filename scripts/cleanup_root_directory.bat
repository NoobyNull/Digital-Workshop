@echo off
REM Digital Workshop Root Directory Cleanup Script (Windows Version)
REM Execute this script to perform the complete cleanup
REM 
REM Usage: cleanup_root_directory.bat
REM 
REM WARNING: This script will reorganize files in the current directory.
REM A backup will be created before any changes are made.

setlocal enabledelayedexpansion

echo Starting Digital Workshop Root Directory Cleanup...
echo.

REM Check if we're in the right directory
if not exist "README.md" (
    echo ERROR: This script must be run from the Digital Workshop root directory
    echo ERROR: README.md not found
    pause
    exit /b 1
)

if not exist "pyproject.toml" (
    echo ERROR: pyproject.toml not found
    pause
    exit /b 1
)

REM Count files before cleanup
for /f %%i in ('dir /b /a-d ^| find /c /v ""') do set BEFORE_COUNT=%%i
echo Current root directory file count: %BEFORE_COUNT% files

REM Phase 1: Backup
echo.
echo Phase 1: Creating backup...
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "BACKUP_DIR=..\digital-workshop-backup-%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
echo Creating backup at: %BACKUP_DIR%
xcopy . "%BACKUP_DIR%" /E /I /Q
if errorlevel 1 (
    echo ERROR: Failed to create backup. Aborting cleanup.
    pause
    exit /b 1
)
echo Backup created successfully

REM Phase 2: Create directory structure
echo.
echo Phase 2: Creating new directory structure...
if not exist "build_system" mkdir "build_system"
if not exist "config" mkdir "config"
if not exist "samples" mkdir "samples"
if not exist "samples\code" mkdir "samples\code"
if not exist "samples\reports" mkdir "samples\reports"
if not exist "build" mkdir "build"
if not exist "build\installer" mkdir "build\installer"
if not exist "build\logs" mkdir "build\logs"
if not exist "archive" mkdir "archive"
if not exist "docs\guides" mkdir "docs\guides"
if not exist "docs\architecture" mkdir "docs\architecture"
if not exist "docs\reports" mkdir "docs\reports"
if not exist "tests\unit" mkdir "tests\unit"
if not exist "tests\integration" mkdir "tests\integration"
if not exist "tests\framework" mkdir "tests\framework"
if not exist "tests\parsers" mkdir "tests\parsers"
if not exist "tests\persistence" mkdir "tests\persistence"
if not exist "tests\themes" mkdir "tests\themes"
if not exist "tests\performance" mkdir "tests\performance"
if not exist "tests\runner" mkdir "tests\runner"
if not exist "reports\json" mkdir "reports\json"
if not exist "reports\html" mkdir "reports\html"
if not exist "reports\analysis" mkdir "reports\analysis"
if not exist "reports\comprehensive" mkdir "reports\comprehensive"
if not exist "reports\performance" mkdir "reports\performance"
if not exist "reports\quality" mkdir "reports\quality"
if not exist "reports\test_results" mkdir "reports\test_results"
if not exist "tools\quality" mkdir "tools\quality"
if not exist "tools\analysis" mkdir "tools\analysis"
if not exist "tools\debug" mkdir "tools\debug"
if not exist "tools\exceptions" mkdir "tools\exceptions"
if not exist "tools\migration" mkdir "tools\migration"
if not exist "tools\demos" mkdir "tools\demos"
if not exist "tools\maintenance" mkdir "tools\maintenance"
echo Directory structure created successfully

REM Phase 3: File movement operations
echo.
echo Phase 3: Moving files to organized structure...

REM Function to safely move files
setlocal
set MOVED_COUNT=0

REM Documentation files
echo Moving documentation files...
if exist "QUICK_START_GUIDE.md" (
    move "QUICK_START_GUIDE.md" "docs\guides\QUICK_START.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: QUICK_START_GUIDE.md
        set /a MOVED_COUNT+=1
    )
)

if exist "REFACTORING_SOLUTIONS.md" (
    move "REFACTORING_SOLUTIONS.md" "docs\guides\REFACTORING.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: REFACTORING_SOLUTIONS.md
        set /a MOVED_COUNT+=1
    )
)

if exist "IMPORT_PROCESS_ARCHITECTURE.md" (
    move "IMPORT_PROCESS_ARCHITECTURE.md" "docs\architecture\IMPORT_PROCESS.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: IMPORT_PROCESS_ARCHITECTURE.md
        set /a MOVED_COUNT+=1
    )
)

if exist "FINAL_IMPLEMENTATION_REPORT.md" (
    move "FINAL_IMPLEMENTATION_REPORT.md" "docs\reports\FINAL_IMPLEMENTATION.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: FINAL_IMPLEMENTATION_REPORT.md
        set /a MOVED_COUNT+=1
    )
)

if exist "WINDOW_PERSISTENCE_TEST_GUIDE.md" (
    move "WINDOW_PERSISTENCE_TEST_GUIDE.md" "docs\guides\WINDOW_PERSISTENCE.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: WINDOW_PERSISTENCE_TEST_GUIDE.md
        set /a MOVED_COUNT+=1
    )
)

if exist "vtk_resource_tracker_fix_summary.md" (
    move "vtk_resource_tracker_fix_summary.md" "docs\reports\VTK_RESOURCE_TRACKER.md" >nul
    if !errorlevel! equ 0 (
        echo Moved: vtk_resource_tracker_fix_summary.md
        set /a MOVED_COUNT+=1
    )
)

REM Test files
echo Moving test files...
if exist "comprehensive_test_suite.py" (
    move "comprehensive_test_suite.py" "tests\integration\" >nul
    if !errorlevel! equ 0 (
        echo Moved: comprehensive_test_suite.py
        set /a MOVED_COUNT+=1
    )
)

if exist "comprehensive_test_suite_tests.py" (
    move "comprehensive_test_suite_tests.py" "tests\integration\" >nul
    if !errorlevel! equ 0 (
        echo Moved: comprehensive_test_suite_tests.py
        set /a MOVED_COUNT+=1
    )
)

if exist "unified_test_runner.py" (
    move "unified_test_runner.py" "tools\maintenance\" >nul
    if !errorlevel! equ 0 (
        echo Moved: unified_test_runner.py
        set /a MOVED_COUNT+=1
    )
)

REM Move test_*.py files
for %%f in (test_*.py) do (
    if exist "%%f" (
        move "%%f" "tests\unit\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Configuration files
echo Moving configuration files...
if exist "quality_config.yaml" (
    move "quality_config.yaml" "config\" >nul
    if !errorlevel! equ 0 (
        echo Moved: quality_config.yaml
        set /a MOVED_COUNT+=1
    )
)

if exist "test_framework_config.json" (
    move "test_framework_config.json" "config\" >nul
    if !errorlevel! equ 0 (
        echo Moved: test_framework_config.json
        set /a MOVED_COUNT+=1
    )
)

if exist "pyinstaller.spec" (
    move "pyinstaller.spec" "build_system\" >nul
    if !errorlevel! equ 0 (
        echo Moved: pyinstaller.spec
        set /a MOVED_COUNT+=1
    )
)

if exist "installer.nsi" (
    move "installer.nsi" "config\" >nul
    if !errorlevel! equ 0 (
        echo Moved: installer.nsi
        set /a MOVED_COUNT+=1
    )
)

REM Sample files
echo Moving sample files...
if exist "sample" (
    move "sample" "samples\" >nul
    if !errorlevel! equ 0 (
        echo Moved: sample directory
        set /a MOVED_COUNT+=1
    )
)

if exist "sample_large_module.py" (
    move "sample_large_module.py" "samples\code\" >nul
    if !errorlevel! equ 0 (
        echo Moved: sample_large_module.py
        set /a MOVED_COUNT+=1
    )
)

if exist "sample_small_module.py" (
    move "sample_small_module.py" "samples\code\" >nul
    if !errorlevel! equ 0 (
        echo Moved: sample_small_module.py
        set /a MOVED_COUNT+=1
    )
)

REM Build files
echo Moving build files...
if exist "installer" (
    move "installer" "build\installer\" >nul
    if !errorlevel! equ 0 (
        echo Moved: installer directory
        set /a MOVED_COUNT+=1
    )
)

REM Move build logs
for %%f in (build_*.log) do (
    if exist "%%f" (
        move "%%f" "build\logs\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Archive temporary files
echo Archiving temporary files...
if exist "mon" (
    move "mon" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: mon
        set /a MOVED_COUNT+=1
    )
)

if exist "n" (
    move "n" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: n
        set /a MOVED_COUNT+=1
    )
)

if exist "P" (
    move "P" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: P
        set /a MOVED_COUNT+=1
    )
)

if exist "validate" (
    move "validate" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: validate
        set /a MOVED_COUNT+=1
    )
)

if exist "quality" (
    move "quality" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: quality
        set /a MOVED_COUNT+=1
    )
)

if exist "-p" (
    move "-p" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: -p directory
        set /a MOVED_COUNT+=1
    )
)

if exist ".augment" (
    move ".augment" "archive\" >nul
    if !errorlevel! equ 0 (
        echo Moved: .augment directory
        set /a MOVED_COUNT+=1
    )
)

REM Move report files in batches
echo Moving report files...

REM JSON reports
for %%f in (*_report.json) do (
    if exist "%%f" (
        move "%%f" "reports\json\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM HTML reports
for %%f in (*_report.html) do (
    if exist "%%f" (
        move "%%f" "reports\html\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Analysis files
for %%f in (*_analysis.json) do (
    if exist "%%f" (
        move "%%f" "reports\analysis\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Comprehensive reports
for %%f in (comprehensive_*_report.md) do (
    if exist "%%f" (
        move "%%f" "reports\comprehensive\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Performance files
for %%f in (performance_*.json) do (
    if exist "%%f" (
        move "%%f" "reports\performance\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Quality files
for %%f in (naming_*.json) do (
    if exist "%%f" (
        move "%%f" "reports\quality\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Test results
for %%f in (test_results.*) do (
    if exist "%%f" (
        move "%%f" "reports\test_results\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

REM Move development tools
echo Moving development tools...
if exist "code_quality_validator.py" (
    move "code_quality_validator.py" "tools\maintenance\" >nul
    if !errorlevel! equ 0 (
        echo Moved: code_quality_validator.py
        set /a MOVED_COUNT+=1
    )
)

if exist "naming_validator.py" (
    move "naming_validator.py" "tools\maintenance\" >nul
    if !errorlevel! equ 0 (
        echo Moved: naming_validator.py
        set /a MOVED_COUNT+=1
    )
)

if exist "quality_gate_enforcer.py" (
    move "quality_gate_enforcer.py" "tools\maintenance\" >nul
    if !errorlevel! equ 0 (
        echo Moved: quality_gate_enforcer.py
        set /a MOVED_COUNT+=1
    )
)

if exist "monolithic_detector.py" (
    move "monolithic_detector.py" "tools\maintenance\" >nul
    if !errorlevel! equ 0 (
        echo Moved: monolithic_detector.py
        set /a MOVED_COUNT+=1
    )
)

if exist "debug_detection.py" (
    move "debug_detection.py" "tools\debug\" >nul
    if !errorlevel! equ 0 (
        echo Moved: debug_detection.py
        set /a MOVED_COUNT+=1
    )
)

if exist "create_exceptions.py" (
    move "create_exceptions.py" "tools\exceptions\" >nul
    if !errorlevel! equ 0 (
        echo Moved: create_exceptions.py
        set /a MOVED_COUNT+=1
    )
)

if exist "migrate_models.py" (
    move "migrate_models.py" "tools\migration\" >nul
    if !errorlevel! equ 0 (
        echo Moved: migrate_models.py
        set /a MOVED_COUNT+=1
    )
)

if exist "monolithic_report.json" (
    move "monolithic_report.json" "tools\analysis\" >nul
    if !errorlevel! equ 0 (
        echo Moved: monolithic_report.json
        set /a MOVED_COUNT+=1
    )
)

REM Error handling demos
for %%f in (error_handling_demo*.py) do (
    if exist "%%f" (
        move "%%f" "tools\demos\" >nul
        if !errorlevel! equ 0 (
            echo Moved: %%f
            set /a MOVED_COUNT+=1
        )
    )
)

endlocal & set MOVED_COUNT=%MOVED_COUNT%

REM Phase 4: Post-cleanup validation
echo.
echo Phase 4: Post-cleanup validation...

REM Count files after cleanup
for /f %%i in ('dir /b /a-d ^| find /c /v ""') do set AFTER_COUNT=%%i
echo Root directory file count after cleanup: %AFTER_COUNT% files
echo Files moved: %MOVED_COUNT%

REM Check essential files are still present
echo Checking essential files...
set MISSING_ESSENTIAL=0

if not exist "README.md" (
    echo ERROR: Essential file missing: README.md
    set /a MISSING_ESSENTIAL+=1
)

if not exist "pyproject.toml" (
    echo ERROR: Essential file missing: pyproject.toml
    set /a MISSING_ESSENTIAL+=1
)

if not exist "requirements.txt" (
    echo ERROR: Essential file missing: requirements.txt
    set /a MISSING_ESSENTIAL+=1
)

if not exist "run.py" (
    echo ERROR: Essential file missing: run.py
    set /a MISSING_ESSENTIAL+=1
)

if not exist "build_system\build.py" (
    echo ERROR: Essential file missing: build_system\build.py
    set /a MISSING_ESSENTIAL+=1
)

if %MISSING_ESSENTIAL% equ 0 (
    echo All essential files present
) else (
    echo ERROR: %MISSING_ESSENTIAL% essential files missing!
)

REM Generate summary report
echo.
echo Generating cleanup summary...
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "SUMMARY_FILE=cleanup_summary_%YYYY%%MM%%DD%_%HH%%Min%%Sec%.txt"

echo Digital Workshop Root Directory Cleanup Summary > "%SUMMARY_FILE%"
echo =============================================== >> "%SUMMARY_FILE%"
echo Date: %YYYY%-%MM%-%DD% %HH%:%Min%:%Sec% >> "%SUMMARY_FILE%"
echo Backup Location: %BACKUP_DIR% >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo File Movement Summary: >> "%SUMMARY_FILE%"
echo - Files before cleanup: %BEFORE_COUNT% >> "%SUMMARY_FILE%"
echo - Files after cleanup: %AFTER_COUNT% >> "%SUMMARY_FILE%"
echo - Files moved: %MOVED_COUNT% >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo Essential Files Status: >> "%SUMMARY_FILE%"
if exist "README.md" (echo - README.md: PRESENT >> "%SUMMARY_FILE%") else (echo - README.md: MISSING >> "%SUMMARY_FILE%")
if exist "pyproject.toml" (echo - pyproject.toml: PRESENT >> "%SUMMARY_FILE%") else (echo - pyproject.toml: MISSING >> "%SUMMARY_FILE%")
if exist "requirements.txt" (echo - requirements.txt: PRESENT >> "%SUMMARY_FILE%") else (echo - requirements.txt: MISSING >> "%SUMMARY_FILE%")
if exist "run.py" (echo - run.py: PRESENT >> "%SUMMARY_FILE%") else (echo - run.py: MISSING >> "%SUMMARY_FILE%")
if exist "build_system\build.py" (echo - build_system\build.py: PRESENT >> "%SUMMARY_FILE%") else (echo - build_system\build.py: MISSING >> "%SUMMARY_FILE%")
echo. >> "%SUMMARY_FILE%"
echo Cleanup completed successfully! >> "%SUMMARY_FILE%"
echo Backup available at: %BACKUP_DIR% >> "%SUMMARY_FILE%"
echo Summary report: %SUMMARY_FILE% >> "%SUMMARY_FILE%"

echo.
echo Cleanup completed successfully!
echo Summary report saved to: %SUMMARY_FILE%
echo Backup available at: %BACKUP_DIR%
echo Root directory now contains %AFTER_COUNT% files (reduced from %BEFORE_COUNT%)

echo.
echo Cleanup plan execution completed!
echo Next steps:
echo 1. Review the cleanup summary: type %SUMMARY_FILE%
echo 2. Test application functionality: python run.py
echo 3. Run test suite: python -m pytest tests/ -v
echo 4. If issues arise, restore from backup: xcopy "%BACKUP_DIR%\*.*" . /E /Y

REM Final validation check
if %AFTER_COUNT% LSS %BEFORE_COUNT% (
    if %MISSING_ESSENTIAL% equ 0 (
        echo.
        echo ✅ CLEANUP SUCCESSFUL - All validation checks passed
        pause
        exit /b 0
    ) else (
        echo.
        echo ⚠️  CLEANUP COMPLETED WITH WARNINGS - Please review the summary
        pause
        exit /b 1
    )
) else (
    echo.
    echo ⚠️  CLEANUP COMPLETED WITH WARNINGS - File count not reduced as expected
    pause
    exit /b 1
)
