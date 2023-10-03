@echo off
cd /d "%~dp0"
call venv\Scripts\activate

echo Running the project...
python Discord_Bot.py

echo Press any key to exit...
pause >nul