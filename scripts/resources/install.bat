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


:: Check if FFmpeg is already installed
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 (
    echo FFmpeg is already installed.
) else (
    :: Create a directory for FFmpeg
    mkdir ffmpeg_install
    cd ffmpeg_install

    :: Download FFmpeg (Replace the URL with the latest version if needed)
    echo Downloading FFmpeg...
    curl -o ffmpeg.zip https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-5.1.2-essentials_build.zip

    :: Unzip FFmpeg
    echo Unzipping FFmpeg...
    tar -xf ffmpeg.zip

    :: Rename and move folder to C:\
    echo Moving FFmpeg to C:\...
    move ffmpeg-5.1.2-essentials_build C:\ffmpeg

    :: Add FFmpeg to system PATH
    echo Adding FFmpeg to PATH...
    setx /M PATH "%PATH%;C:\ffmpeg\bin"

    :: Clean up
    cd ..
    rmdir /S /Q ffmpeg_install
    echo FFmpeg installation complete!
)



setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Uncomment this if you want to delete existing folder before cloning
:: rmdir /s /q "Aetherius_AI_Assistant"

echo Cloning the repository...
git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git
cd Aetherius_AI_Assistant

:: Create a virtual environment
python -m venv "venv"

:: Install project dependencies
"venv\Scripts\python" -m pip install -r requirements.txt
"venv\Scripts\python" -m pip install --upgrade numpy==1.24

:: Run the project
"venv\Scripts\python" main.py

echo Press any key to exit...
pause >nul
goto :EOF