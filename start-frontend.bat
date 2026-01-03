@echo off
REM Start Vue.js Frontend Server

echo ========================================
echo Starting Vue.js Frontend Server
echo ========================================
echo.
echo Frontend application will be available at:
echo http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

cd frontend
npm run dev
