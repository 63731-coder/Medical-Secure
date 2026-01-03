@echo off
REM Start Django Backend Server

echo ========================================
echo Starting Django Backend Server
echo ========================================
echo.
echo Backend API will be available at:
echo http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
call venv\Scripts\activate
python manage.py runserver
