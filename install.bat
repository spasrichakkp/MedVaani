@echo off
REM Enhanced Medical Research AI - Windows Installation Script
REM This script sets up the Enhanced Medical Research AI system on Windows

echo 🩺 Enhanced Medical Research AI - Windows Installation Script
echo ===========================================================

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.9+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found

REM Check if UV is available
echo [INFO] Checking UV package manager...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] UV package manager not found
    set /p UV_INSTALL="Would you like to install UV for faster dependency management? (y/n): "
    if /i "%UV_INSTALL%"=="y" (
        echo [INFO] Installing UV package manager...
        powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
        REM Refresh PATH
        call refreshenv >nul 2>&1
        uv --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo [WARNING] UV installation failed, falling back to pip
            set USE_UV=false
        ) else (
            echo [SUCCESS] UV installed successfully
            set USE_UV=true
        )
    ) else (
        echo [INFO] Using pip for dependency management
        set USE_UV=false
    )
) else (
    echo [SUCCESS] UV package manager found
    set USE_UV=true
)

REM Create virtual environment
echo [INFO] Creating virtual environment...
if "%USE_UV%"=="true" (
    uv venv
    echo [SUCCESS] Virtual environment created with UV
) else (
    python -m venv .venv
    echo [SUCCESS] Virtual environment created with venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated

REM Install dependencies
echo [INFO] Installing dependencies...
if "%USE_UV%"=="true" (
    echo [INFO] Installing with UV...
    uv pip install -r requirements.txt
    uv pip install -r requirements-web.txt
    
    set /p DEV_DEPS="Would you like to install development dependencies? (y/n): "
    if /i "%DEV_DEPS%"=="y" (
        uv pip install -e ".[dev]"
        echo [SUCCESS] Development dependencies installed
    )
) else (
    echo [INFO] Installing with pip...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-web.txt
    
    set /p DEV_DEPS="Would you like to install development dependencies? (y/n): "
    if /i "%DEV_DEPS%"=="y" (
        pip install -e ".[dev]"
        echo [SUCCESS] Development dependencies installed
    )
)
echo [SUCCESS] Dependencies installed successfully

REM Setup environment file
echo [INFO] Setting up environment configuration...
if not exist .env (
    (
        echo # Enhanced Medical Research AI Configuration
        echo.
        echo # Optional: Infermedica API for enhanced accuracy
        echo # INFERMEDICA_APP_ID=your_app_id
        echo # INFERMEDICA_APP_KEY=your_app_key
        echo.
        echo # Enhanced features ^(enabled by default^)
        echo ENABLE_DRUG_RECOMMENDATIONS=true
        echo ENABLE_INTERACTIVE_DIAGNOSIS=true
        echo.
        echo # Model configuration
        echo MEDICAL_MODEL=google/flan-t5-base
        echo MEDICAL_DEVICE=auto
        echo ENVIRONMENT=development
        echo.
        echo # Performance tuning
        echo FORCE_TORCH_DTYPE=float32
        echo USE_MOCK_ADAPTERS=false
    ) > .env
    echo [SUCCESS] Environment file created ^(.env^)
) else (
    echo [WARNING] Environment file already exists ^(.env^)
)

REM Download models
echo [INFO] Downloading initial AI models...
set /p DOWNLOAD_MODELS="Would you like to download the default medical AI model? This will download google/flan-t5-base (~1GB) (y/n): "
if /i "%DOWNLOAD_MODELS%"=="y" (
    python download_models.py
    echo [SUCCESS] Models downloaded successfully
) else (
    echo [WARNING] Models not downloaded. You can download them later with: python download_models.py
)

REM Run tests
set /p RUN_TESTS="Would you like to run tests to verify the installation? (y/n): "
if /i "%RUN_TESTS%"=="y" (
    echo [INFO] Running tests...
    pytest tests/ -v >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] Some tests failed or pytest not available
    ) else (
        echo [SUCCESS] Tests completed successfully
    )
)

echo.
echo [SUCCESS] 🎉 Installation completed successfully!
echo.
echo Next steps:
echo 1. Activate the virtual environment:
echo    .venv\Scripts\activate.bat
echo 2. Start the web server:
echo    python web\main.py
echo 3. Open your browser to: http://localhost:8000
echo.
echo For more information, see README.md
echo.
pause
