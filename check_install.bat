@echo off
setlocal EnableDelayedExpansion

echo ==================================================
echo  CMakeCraft - environment check and install helper
echo ==================================================

REM Determine Python command (prefer py -3 launcher)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set "PY=py"
    set "PY_VER_ARG=-3"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
        set "PY=python"
        set "PY_VER_ARG="
    ) else (
        echo ERROR: Python 3.8+ not found in PATH.
        echo Please install Python 3.8 or newer: https://www.python.org/downloads/
        exit /b 1
    )
)

echo Using Python command: %PY% %PY_VER_ARG%

REM Check Python version >= 3.8
%PY% %PY_VER_ARG% -c "import sys; sys.exit(0 if (sys.version_info[0]>3 or (sys.version_info[0]==3 and sys.version_info[1]>=8)) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3.8 or newer is required.
    %PY% %PY_VER_ARG% --version
    exit /b 1
)

REM Check for CMake (optional)
where cmake >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: CMake not found in PATH. CMake is required to build the C++ examples.
    echo Install CMake from: https://cmake.org/download/
) else (
    for /f "usebackq tokens=*" %%i in (`cmake --version`) do (
        echo Found: %%i
        goto :cmake_checked
    )
)
:cmake_checked

REM Create virtual environment if missing
if not exist venv\Scripts\python.exe (
    echo Creating virtual environment in .\venv ...
    %PY% %PY_VER_ARG% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo Virtual environment found at .\venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install requirements if present
if exist requirements.txt (
    echo Installing Python requirements from requirements.txt ...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: pip install failed. See output above.
        exit /b 1
    )
) else (
    echo No requirements.txt found. Skipping pip install.
    REM Ensure core dependency 'textual' is installed (used by the TUI)
    echo Checking for 'textual' package...
    python -c "import textual" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo 'textual' not found. Installing 'textual'...
        pip install textual
        if %ERRORLEVEL% NEQ 0 (
            echo ERROR: Failed to install 'textual'.
            exit /b 1
        )
    ) else (
        echo 'textual' is already installed.
    )
)

echo
echo All set. To activate the environment later, run:
echo    call venv\Scripts\activate.bat
echo To run the example build (Windows), ensure CMake is installed and use your preferred build steps.
echo Done.

endlocal
