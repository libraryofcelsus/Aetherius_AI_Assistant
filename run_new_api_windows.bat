@echo off
cd /d "%~dp0"
call venv\Scripts\activate


echo Starting ngrok tunnel with reserved subdomain: %SUBDOMAIN%
start ngrok start Aetherius

echo Running the project...
python New_API.py

echo Press any key to exit...
pause >nul