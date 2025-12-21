# SecureMed Makefile for Ubuntu 22.04 x64
# Usage: make [target]

.PHONY: help install setup-backend setup-frontend setup-keycloak start-keycloak start-backend start-frontend stop clean sync-users

help:
	@echo "SecureMed - Available commands:"
	@echo "  make install         - Install all dependencies and setup the project"
	@echo "  make setup-backend   - Setup Django backend (venv, dependencies, migrations)"
	@echo "  make setup-frontend  - Setup Vue.js frontend (npm install)"
	@echo "  make setup-keycloak  - Start Keycloak with Docker Compose"
	@echo "  make start-keycloak  - Start Keycloak containers"
	@echo "  make start-backend   - Start Django development server"
	@echo "  make start-frontend  - Start Vue.js development server"
	@echo "  make stop            - Stop all Docker containers"
	@echo "  make sync-users      - Synchronize users from Keycloak to Django"
	@echo "  make clean           - Remove virtual environment and node_modules"

# Full installation
install: setup-backend setup-frontend setup-keycloak
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "To start the application:"
	@echo "  Terminal 1: make start-keycloak"
	@echo "  Terminal 2: make start-backend"
	@echo "  Terminal 3: make start-frontend"

# Backend setup
setup-backend:
	@echo "🔧 Setting up Django backend..."
	cd backend && python3 -m venv venv
	cd backend && . venv/bin/activate && pip install --upgrade pip
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "📝 Creating .env file..."
	@if [ ! -f backend/.env ]; then \
		echo "DJANGO_SECRET_KEY=django-insecure-dev-key-$(shell date +%s)" > backend/.env; \
		echo "KEYCLOAK_SERVER_URL=http://localhost:8080" >> backend/.env; \
		echo "KEYCLOAK_REALM=medical-realm" >> backend/.env; \
		echo "KEYCLOAK_CLIENT_ID=medical-app" >> backend/.env; \
		echo "KEYCLOAK_CLIENT_SECRET=OESLG5iTt2FSRegpLhgRRTvKY7eugLpt" >> backend/.env; \
		echo "KEYCLOAK_REDIRECT_URI=http://localhost:5173/callback" >> backend/.env; \
		echo ".env file created"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo "🗄️  Running migrations..."
	cd backend && . venv/bin/activate && python manage.py migrate
	@echo "✅ Backend setup complete!"

# Frontend setup
setup-frontend:
	@echo "🔧 Setting up Vue.js frontend..."
	cd frontend && npm install
	@echo "✅ Frontend setup complete!"

# Keycloak setup
setup-keycloak:
	@echo "🔧 Setting up Keycloak..."
	@if ! command -v docker &> /dev/null; then \
		echo "❌ Docker is not installed. Please install Docker first."; \
		exit 1; \
	fi
	docker-compose up -d
	@echo "⏳ Waiting for Keycloak to start (60 seconds)..."
	@sleep 60
	@echo "✅ Keycloak setup complete!"
	@echo "   Keycloak Admin: http://localhost:8080"
	@echo "   Username: admin"
	@echo "   Password: admin123"

# Start Keycloak
start-keycloak:
	@echo "🚀 Starting Keycloak..."
	docker-compose up

# Start backend server
start-backend:
	@echo "🚀 Starting Django backend..."
	@echo "   Backend API: http://127.0.0.1:8000"
	cd backend && . venv/bin/activate && python manage.py runserver

# Start frontend server
start-frontend:
	@echo "🚀 Starting Vue.js frontend..."
	@echo "   Frontend App: http://localhost:5173"
	cd frontend && npm run dev

# Stop all containers
stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down
	@echo "✅ Containers stopped!"

# Sync users from Keycloak
sync-users:
	@echo "🔄 Synchronizing users from Keycloak..."
	cd backend && . venv/bin/activate && python sync_users.py

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -f backend/db.sqlite3
	docker-compose down -v
	@echo "✅ Cleanup complete!"
