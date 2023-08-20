@echo off
:: Check if Git is already installed
where git >nul 2>nul
if %errorlevel% equ 0 (
    echo Git is already installed.
) else (
    :: Download Git installer
    echo Downloading Git installer...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/Git-2.41.0.3-64-bit.exe' -OutFile '%TEMP%\GitInstaller.exe'"

    :: Install Git
    echo Installing Git...
    %TEMP%\GitInstaller.exe /SILENT /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"

    :: Delete the installer
    del %TEMP%\GitInstaller.exe
)



setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Uncomment this if you want to delete existing folder before cloning
:: rmdir /s /q "Aetherius_AI_Assistant"

echo Cloning the repository...
git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git || goto :error
cd Aetherius_AI_Assistant

:: Initialize PYTHON_PATH as empty
set PYTHON_PATH=

:: Manually specify paths to ignore
set IGNORE_PATH=C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe

echo Checking known locations...
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo Found Python at: %%i
    if not "%%i"=="!IGNORE_PATH!" (
        set PYTHON_PATH=%%i
        echo Set PYTHON_PATH to !PYTHON_PATH!
    ) else (
        echo Ignoring Python at: %%i
    )
)

:: Check if PYTHON_PATH was set
if not defined PYTHON_PATH (
    echo No acceptable Python installation found.
    echo Installing Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe' -OutFile 'python-installer.exe'; Start-Process 'python-installer.exe' -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 TargetDir=%APPDATA%\Python\Python310' -Wait; Remove-Item 'python-installer.exe';"
    set PYTHON_PATH=%APPDATA%\Python\Python310\python.exe
    echo Set PYTHON_PATH to !PYTHON_PATH!
)

:: In case Python is not found or installed, terminate the script
if not defined PYTHON_PATH (
    echo Python was not found or installed. Exiting...
    goto :error
)

echo Python is already installed at !PYTHON_PATH!.

:: Create a virtual environment
"!PYTHON_PATH!" -m venv "venv"

:: Install project dependencies
"venv\Scripts\python" -m pip install -r requirements.txt

:: Run the project
"venv\Scripts\python" main.py

echo Press any key to exit...
pause >nul
goto :EOF

:error
echo An error occurred. Exiting...
pause >nul