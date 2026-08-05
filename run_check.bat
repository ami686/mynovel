@echo off
cd /d "%~dp0"
echo Checking for duplicate folder names in content directory...
echo.
python check_dup_folders.py content
echo.
echo Done. Press any key to close this window...
pause >nul
