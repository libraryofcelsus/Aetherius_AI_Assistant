@echo off
cd /d "%~dp0"
call venv\Scripts\activate

:: Check if the gradio library is installed
python -c "import pkg_resources; pkg_resources.get_distribution('gradio')" >nul 2>&1
if %errorlevel% neq 0 (
    echo Gradio library not found, installing...
    pip install gradio
) else (
    echo Gradio library is already installed.
)

echo Running the project...
python Gradio-Ui.py

echo Press any key to exit...
pause >nul