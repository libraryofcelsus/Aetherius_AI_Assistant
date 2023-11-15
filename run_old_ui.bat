@echo off
cd /d "%~dp0"
call venv\Scripts\activate

cd Old_Ui

echo Running the project...
python main.py

echo Press any key to exit...
pause >nul
