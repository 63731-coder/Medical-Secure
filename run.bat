@echo off
REM Run script for Medical Secure on Windows 10

echo =====================================
echo Medical Secure - Starting Application
echo =====================================
echo.

REM Check if Docker services are running
docker ps | findstr medical-postgres >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting Docker services (PostgreSQL, Keycloak^)...
    docker-compose up -d
    echo Waiting for services to be ready...
    timeout /t 10 /nobreak >nul
) else (
    echo Docker services are already running
)

echo Starting backend server...
start "Medical Secure Backend" cmd /k "cd backend && python manage.py runserver 0.0.0.0:8000"

echo Starting frontend server...
start "Medical Secure Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =====================================
echo Application is running!
echo =====================================
echo.
echo Backend API: http://localhost:8000
echo Frontend App: http://localhost:5173
echo Keycloak Admin: http://localhost:8080
echo.
echo Two new terminal windows have been opened.
echo Close those windows to stop the servers.
echo.
pause
