@echo off
cd /d "%~dp0"
call venv\Scripts\activate


echo Running the project...
python Aetherius_Terminal_Mode.py

echo Press any key to exit...
pause >nul