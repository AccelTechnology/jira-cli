@echo off
setlocal enabledelayedexpansion

echo Installing Jira CLI for Windows...
echo.

REM Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo Error: Python is required but not found in PATH.
        echo Please install Python 3.8 or higher from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Check Python version
echo Checking Python version...
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if %errorlevel% neq 0 (
    for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%i
    echo Error: Python 3.8 or higher is required. Found: Python !PYTHON_VERSION!
    echo Please upgrade your Python installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PYTHON_VERSION=%%i
echo Python version check passed: !PYTHON_VERSION!

REM Check if pip is available
%PYTHON_CMD% -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: pip is required but not available.
    echo Please ensure pip is installed with your Python installation.
    pause
    exit /b 1
)

REM Offer to create virtual environment
echo.
set /p CREATE_VENV="Do you want to create a virtual environment? (recommended) [Y/n]: "
if /i "!CREATE_VENV!"=="" set CREATE_VENV=y
if /i "!CREATE_VENV!"=="y" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv jira-cli-venv
    if %errorlevel% neq 0 (
        echo Warning: Failed to create virtual environment. Proceeding with global installation.
    ) else (
        echo Activating virtual environment...
        call jira-cli-venv\Scripts\activate.bat
        echo Virtual environment activated.
        echo To activate it manually later, run: jira-cli-venv\Scripts\activate.bat
    )
)

REM Install the package
echo.
echo Installing jira-cli...
%PYTHON_CMD% -m pip install -e .
if %errorlevel% neq 0 (
    echo Error: Installation failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Installation completed successfully!
echo ============================================
echo.
echo Usage:
echo   jira-cli --help                           # Show help
echo   jira-cli auth test                        # Test connection
echo   jira-cli epics                            # List epics
echo   jira-cli my-issues                        # List your issues
echo   jira-cli search "project=YOUR_PROJECT"    # Search issues
echo.
echo Configuration:
echo Set these environment variables (you can add them to your system or use a .env file):
echo   set JIRA_EMAIL=your.email@example.com
echo   set JIRA_API_TOKEN=your_api_token
echo   set JIRA_URL=https://your-domain.atlassian.net
echo.
echo To set environment variables permanently:
echo   1. Open System Properties ^> Advanced ^> Environment Variables
echo   2. Add the variables under "User variables"
echo   3. Restart your command prompt
echo.
if /i "!CREATE_VENV!"=="y" (
    echo Note: Virtual environment created in 'jira-cli-venv' directory.
    echo Remember to activate it before using jira-cli: jira-cli-venv\Scripts\activate.bat
)
echo.
pause