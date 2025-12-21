#!/bin/bash
# SecureMed Setup Script for Ubuntu 22.04 x64
# This script installs dependencies and sets up the project

set -e  # Exit on error

echo "========================================"
echo "SecureMed - Installation Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed"
    echo "Please run: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed"
    echo "Please run: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install nodejs"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed"
    echo "Please run: sudo apt install docker.io docker-compose"
    exit 1
fi

echo "[1/4] Setting up Django backend..."
echo ""

# Setup backend
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DJANGO_SECRET_KEY=django-insecure-dev-key-$(date +%s)
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=medical-realm
KEYCLOAK_CLIENT_ID=medical-app
KEYCLOAK_CLIENT_SECRET=OESLG5iTt2FSRegpLhgRRTvKY7eugLpt
KEYCLOAK_REDIRECT_URI=http://localhost:5173/callback
EOF
    echo ".env file created"
else
    echo ".env file already exists"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate

cd ..
echo "[OK] Backend setup complete!"
echo ""

echo "[2/4] Setting up Vue.js frontend..."
echo ""

# Setup frontend
cd frontend
echo "Installing Node.js dependencies..."
npm install
cd ..

echo "[OK] Frontend setup complete!"
echo ""

echo "[3/4] Setting up Keycloak..."
echo ""

# Start Keycloak
echo "Starting Keycloak with Docker Compose..."
docker-compose up -d

echo "Waiting for Keycloak to start (60 seconds)..."
sleep 60

echo "[OK] Keycloak setup complete!"
echo ""

echo "[4/4] Installation Summary"
echo "========================================"
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "Keycloak: http://localhost:8080"
echo "  Admin username: admin"
echo "  Admin password: admin123"
echo "========================================"
echo ""
echo "Installation complete!"
echo ""
echo "To start the application:"
echo "  Terminal 1: cd backend && source venv/bin/activate && python manage.py runserver"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
echo "Or use the Makefile:"
echo "  Terminal 1: make start-backend"
echo "  Terminal 2: make start-frontend"
echo ""
echo "To stop Keycloak: docker-compose down"
echo ""
