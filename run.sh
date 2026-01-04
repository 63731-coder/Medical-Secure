#!/bin/bash
# Run script for Medical Secure

echo "====================================="
echo "Medical Secure - Starting Application"
echo "====================================="
echo ""

# Check if Docker services are running
if ! docker ps | grep -q medical-postgres; then
    echo "Starting Docker services (PostgreSQL, Keycloak)..."
    docker-compose up -d
    echo "Waiting for services to be ready..."
    sleep 10
else
    echo "Docker services are already running"
fi

echo "Starting backend server..."
cd backend
python3 manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "====================================="
echo "Application is running!"
echo "====================================="
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:5173"
echo "Keycloak Admin: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers..."
echo ""

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
