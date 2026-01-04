#!/bin/bash
# Setup script for Medical Secure on Ubuntu 22.04

set -e  # Exit on error

echo "====================================="
echo "Medical Secure - Setup Script"
echo "====================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
else
    echo "✓ Docker is already installed"
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installing..."
    sudo apt-get install -y python3 python3-pip
else
    echo "✓ Python 3 is already installed"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "✓ Node.js is already installed"
fi

echo ""
echo "Starting Docker services (PostgreSQL, Keycloak)..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo ""
echo "Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt

echo ""
echo "Running database migrations..."
python3 manage.py migrate

echo ""
echo "Installing frontend dependencies..."
cd ../frontend
npm install

echo ""
echo "====================================="
echo "Setup completed successfully!"
echo "====================================="
echo ""
echo "To start the application, run:"
echo "  ./run.sh"
echo ""
