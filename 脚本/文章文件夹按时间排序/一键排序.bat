@echo off
chcp 65001 >nul

if "%~1"=="" (
    echo Please drag your category folder onto this bat file.
    echo.
    pause
    exit /b
)

set "TARGET=%~1"

echo Checking / installing dependencies, please wait...
python -m pip install pyyaml --break-system-packages -q

echo.
echo ================= PREVIEW ONLY - nothing changed yet =================
python "%~dp0rename_bundles_by_date.py" "%TARGET%" --dry-run
echo ========================================================================
echo.

set /p CONFIRM=Type Y and press Enter to CONFIRM rename, or press Enter to cancel: 

if /i "%CONFIRM%"=="Y" (
    echo.
    echo Renaming now...
    python "%~dp0rename_bundles_by_date.py" "%TARGET%"
    echo.
    echo Done. Please check the folder.
) else (
    echo Cancelled. Nothing was changed.
)

echo.
pause
