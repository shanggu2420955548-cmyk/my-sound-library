@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_EXE="

if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "runtime\python\python.exe" set "PYTHON_EXE=runtime\python\python.exe"

if not defined PYTHON_EXE (
    for /f "delims=" %%P in ('where python.exe 2^>nul') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo ERROR: Python was not found.
    echo Install Python 3.11/3.12, or create .venv in this project.
    echo.
    echo Suggested setup:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install --upgrade pip
    echo   .venv\Scripts\python.exe -m pip install -r requirements-dev-minimal.txt
    pause
    exit /b 1
)

"%PYTHON_EXE%" --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: Selected Python could not run:
    echo   %PYTHON_EXE%
    echo.
    echo If this points to WindowsApps, install Python from python.org and reopen the terminal.
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%;%PYTHONPATH%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

"%PYTHON_EXE%" -c "import PySide6, qfluentwidgets, qframelesswindow" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Required GUI dependencies are missing.
    echo.
    echo Run:
    echo   "%PYTHON_EXE%" -m pip install -r requirements-dev-minimal.txt
    pause
    exit /b 1
)

echo Starting My Sound Library in development mode...
"%PYTHON_EXE%" -m transcriptionist_v3 %*

if errorlevel 1 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)

endlocal
