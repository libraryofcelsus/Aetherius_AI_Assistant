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



cd /d "%~dp0"
echo Cloning the repository...
git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git
cd /d "%~dp0Aetherius_AI_Assistant"


setlocal

:: Manually specify paths to ignore
set IGNORE_PATH=C:\Users\%USERNAME%\AppData\Local\Microsoft\WindowsApps\python.exe

echo Checking known locations...
:: Automatically find Python path in known locations
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo Found Python at: %%i
    if not "%%i"=="%IGNORE_PATH%" (
        set PYTHON_PATH=%%i
        echo Set PYTHON_PATH to %%i
        goto :foundPython
    ) else (
        echo Ignoring Python at: %%i
    )
)

echo Checking AppData...
:: If not found, then check AppData
if not defined PYTHON_PATH (
    for %%X in (310 39 38 37 36) do (
        if exist "%APPDATA%\Python\Python%%X\python.exe" (
            echo Found Python in AppData at: %APPDATA%\Python\Python%%X\python.exe
            set PYTHON_PATH=%APPDATA%\Python\Python%%X\python.exe
            echo Set PYTHON_PATH to %APPDATA%\Python\Python%%X\python.exe
            goto :foundPython
        )
    )
)

:: If Python was found in any of the locations
:foundPython
if defined PYTHON_PATH (
    echo Python is already installed at %PYTHON_PATH%.
    goto :end
) else (
    echo Installing Python...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.6/python-3.10.6-amd64.exe' -OutFile 'python-installer.exe'; Start-Process 'python-installer.exe' -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1 TargetDir=%APPDATA%\Python\Python310' -Wait; Remove-Item 'python-installer.exe';"
    if errorlevel 1 (
        echo Failed to install Python.
        goto :end
    )
    echo Python installed at %APPDATA%\Python\Python310\python.exe
    set PYTHON_PATH=%APPDATA%\Python\Python310\python.exe
    echo Set PYTHON_PATH to %APPDATA%\Python\Python310\python.exe
)

:end
endlocal


echo Creating a virtual environment...
python -m venv "%~dp0Aetherius_AI_Assistant\venv"

echo Installing project dependencies...
venv\Scripts\python -m pip install -r requirements.txt

echo Running the project...
"%~dp0Aetherius_AI_Assistant\venv\Scripts\python.exe" main.py

echo Press any key to exit...
pause >nul