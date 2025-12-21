@echo off
REM SecureMed Setup Script for Windows 10 x64
REM This script installs dependencies and sets up the project

echo ========================================
echo SecureMed - Installation Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo [1/4] Setting up Django backend...
echo.

REM Setup backend
cd backend

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    (
        echo DJANGO_SECRET_KEY=django-insecure-dev-key-change-in-production
        echo KEYCLOAK_SERVER_URL=http://localhost:8080
        echo KEYCLOAK_REALM=medical-realm
        echo KEYCLOAK_CLIENT_ID=medical-app
        echo KEYCLOAK_CLIENT_SECRET=OESLG5iTt2FSRegpLhgRRTvKY7eugLpt
        echo KEYCLOAK_REDIRECT_URI=http://localhost:5173/callback
    ) > .env
    echo .env file created
) else (
    echo .env file already exists
)

REM Run migrations
echo Running database migrations...
python manage.py migrate

cd ..
echo [OK] Backend setup complete!
echo.

echo [2/4] Setting up Vue.js frontend...
echo.

REM Setup frontend
cd frontend
echo Installing Node.js dependencies...
call npm install
cd ..

echo [OK] Frontend setup complete!
echo.

echo [3/4] Setting up Keycloak...
echo.

REM Start Keycloak
echo Starting Keycloak with Docker Compose...
docker-compose up -d

echo Waiting for Keycloak to start (60 seconds)...
timeout /t 60 /nobreak >nul

echo [OK] Keycloak setup complete!
echo.

echo [4/4] Installation Summary
echo ========================================
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo Keycloak: http://localhost:8080
echo   Admin username: admin
echo   Admin password: admin123
echo ========================================
echo.
echo Installation complete!
echo.
echo To start the application, run:
echo   start-backend.bat   (in Terminal 1)
echo   start-frontend.bat  (in Terminal 2)
echo.
echo To stop Keycloak:
echo   docker-compose down
echo.
pause
