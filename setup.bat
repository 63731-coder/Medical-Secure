@echo off
REM Setup script for Medical Secure on Windows 10

echo =====================================
echo Medical Secure - Setup Script
echo =====================================
echo:

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker not found. Please install Docker Desktop from:
    echo https://www.docker.com/products/docker-desktop
    echo.
    echo After installing Docker Desktop, run this script again.
    pause
    exit /b 1
) else (
    echo [OK] Docker is installed
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10+ from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    echo [OK] Python is installed
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found. Please install Node.js 20.x from:
    echo https://nodejs.org/
    pause
    exit /b 1
) else (
    echo [OK] Node.js is installed
)

echo:
echo Starting Docker services (PostgreSQL, Keycloak)...
docker-compose up -d

echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo:
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt

echo:
echo Running database migrations...
python manage.py migrate

echo:
echo Installing frontend dependencies...
cd ..\frontend
call npm install

echo:
echo =====================================
echo Setup completed successfully!
echo =====================================
echo:
echo To start the application, run:
echo   run.bat
echo:
pause
