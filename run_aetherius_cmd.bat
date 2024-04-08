@echo off
cd /d "%~dp0"
call venv\Scripts\activate

cmd /k

echo Press any key to exit...
pause >nul