@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Running check...
python check_dup_folders.py content
echo.
echo Done. Press any key to close...
pause >nul
