@echo off
rem Build: regenerate index.html from essays/*.md and site-config.json
cd /d "%~dp0"

set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
if not defined PY set "PY=python"

"%PY%" build.py
if errorlevel 1 (
  echo.
  echo Build FAILED: Python was not found. Please install Python 3.
  echo (Install from python.org, or tell the assistant to install it.)
)
pause
