@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  JMV Agent - Windows EXE Auto Build
echo ============================================================

:: Step 1: Find Python 3.11
set PY311=

for %%P in (
    "C:\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
    "%PROGRAMFILES(X86)%\Python311\python.exe"
) do (
    if exist %%P (
        set PY311=%%~P
        goto :found_py311
    )
)

:: Not found - try winget
echo [Step 1] Python 3.11 not found. Installing via winget...
winget --version >/dev/null 2>&1
if errorlevel 1 (
    echo [ERROR] winget not available.
    echo Please install Python 3.11.9 manually from:
    echo   https://www.python.org/downloads/release/python-3119/
    pause
    exit /b 1
)

winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo [ERROR] winget install failed. Please install manually.
    pause
    exit /b 1
)

for %%P in (
    "C:\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
) do (
    if exist %%P (
        set PY311=%%~P
        goto :found_py311
    )
)

echo [ERROR] Python 3.11 not found after install. Restart terminal and retry.
pause
exit /b 1

:found_py311
echo [Step 1] Python 3.11 found: %PY311%
"%PY311%" --version

:: Step 2: Create venv
if not exist "venv311\Scripts\activate.bat" (
    echo [Step 2] Creating venv311...
    "%PY311%" -m venv venv311
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
) else (
    echo [Step 2] venv311 already exists, skipping.
)

:: Step 3: Install deps
echo [Step 3] Installing Kivy 2.3.0 + PyInstaller...
call venv311\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
python -m pip install "kivy[base]==2.3.0"
if errorlevel 1 (
    echo [ERROR] Kivy install failed. Check network.
    pause
    exit /b 1
)

python -m pip install "pyinstaller>=6.0.0"
if errorlevel 1 (
    echo [ERROR] PyInstaller install failed.
    pause
    exit /b 1
)

python -c "import kivy; print('[OK] Kivy', kivy.__version__)"
if errorlevel 1 (
    echo [ERROR] Kivy import failed.
    pause
    exit /b 1
)

:: Step 4: Package
echo [Step 4] Building EXE...
pyinstaller brain_agent.spec --clean --noconfirm

if exist "dist\BrainAgent.exe" (
    echo.
    echo ============================================================
    echo  [SUCCESS] Windows EXE built: dist\BrainAgent.exe
    echo ============================================================
    exit /b 0
) else (
    echo [ERROR] Build failed. See errors above.
    pause
    exit /b 1
)
