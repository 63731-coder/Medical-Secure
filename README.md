# Medical Secure - Secure Medical Records Management System

## Group Members

- **63731** - Nicoleta Opre
- **60991** - Aninia Negue
- **62834** - Damian Wesolowski
- **62642** - Christophe Antar
- **62755** - Adam Moussa

## Project Description

Medical Secure is a secure medical records management system that allows doctors and patients to manage medical records with end-to-end encryption. The system consists of a Django backend API and a Vue.js frontend application.

### Architecture

The application consists of three main components:

1. **Backend (Django REST API)** - Port 8000
   - Handles business logic and data management
   - Implements end-to-end encryption for medical records
   - Integrates with Keycloak for authentication
   - Connects to PostgreSQL database

2. **Frontend (Vue.js SPA)** - Port 5173
   - Modern single-page application
   - User interface for doctors and patients
   - Client-side encryption/decryption of medical data

3. **Authentication (Keycloak)** - Port 8080
   - Identity and access management
   - Pre-configured realm with doctor and patient roles
   - OAuth 2.0 / OpenID Connect authentication

4. **Database (PostgreSQL)** - Port 5432
   - Stores encrypted medical records
   - User data and relationships

## Quick Start

Get the application running in 3 steps:

```bash
# 1. Start Docker services (PostgreSQL, Keycloak)
docker-compose up -d

# 2. Setup backend (install deps, configure, migrate DB)
cd backend
pip install -r requirements.txt
python manage.py migrate

# 3. Setup and run frontend
cd ../frontend
npm install
npm run dev
```

Then open http://localhost:5173 in your browser!

> **Windows users**: Use `setup.bat` and `run.bat` scripts for automated setup.

## Prerequisites

### For Ubuntu 22.04 (x64)

- Python 3.10 or higher
- Node.js 20.x or higher
- PostgreSQL 15
- Keycloak 23.0
- Docker and Docker Compose (recommended)

### For Windows 10 (x64)

- Python 3.10 or higher
- Node.js 20.x or higher
- PostgreSQL 15
- Keycloak 23.0
- Docker Desktop (recommended)

## Building the Project

### Quick Setup (Recommended)

We provide automated setup scripts that will install dependencies, configure the database, and prepare the project.

**On Ubuntu 22.04:**
```bash
chmod +x setup.sh run.sh
./setup.sh
```

**On Windows 10:**
```cmd
setup.bat
```

The setup script will:
- Check and install required dependencies (Docker, Python, Node.js)
- Start Docker services (PostgreSQL, Keycloak)
- Install Python packages
- Run database migrations
- Install Node.js packages

### Manual Setup

If you prefer to set up manually:

1. **Install Docker and Docker Compose**
   - Ubuntu: `sudo apt-get install docker.io docker-compose`
   - Windows: Install Docker Desktop from https://www.docker.com/products/docker-desktop

2. **Start Docker services (PostgreSQL, Keycloak)**
   ```bash
   docker-compose up -d
   ```
   
   Wait ~10 seconds for services to be ready.

3. **Environment variables (already configured)**
   
   The `backend/.env` file is already included in the repository with all necessary configuration:
   - **Django settings**: SECRET_KEY, DEBUG, ALLOWED_HOSTS
   - **Database credentials**: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
   - **Keycloak configuration**: KEYCLOAK_SERVER_URL, KEYCLOAK_REALM, KEYCLOAK_CLIENT_ID, KEYCLOAK_CLIENT_SECRET
   

4. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

## Running the Project

### Quick Start (Recommended)

After running the setup script, you can start the application using:

**On Ubuntu 22.04:**
```bash
./run.sh
```

**On Windows 10:**
```cmd
run.bat
```

The run script will automatically:
- Start Docker services: PostgreSQL and Keycloak (if not running)
- Launch the backend server on port 8000
- Launch the frontend development server on port 5173

Access the application at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Keycloak Admin Console**: http://localhost:8080 (admin/admin123)

### Manual Start

If you prefer to start the servers manually:

**Start the Backend Server:**

On Ubuntu:
```bash
cd backend
python3 manage.py runserver 0.0.0.0:8000
```

On Windows:
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

The backend API will be available at http://localhost:8000

**Start the Frontend Development Server:**

On both Ubuntu and Windows:
```bash
cd frontend
npm run dev
```

The frontend application will be available at http://localhost:5173

## Usage

1. **Access the application**
   - Open your web browser and navigate to http://localhost:5173

2. **Access Keycloak Admin Console** (if needed)
   - URL: http://localhost:8080
   - Username: `admin`
   - Password: `admin123`
   - The `medical-realm` is automatically imported with pre-configured users and roles

3. **Register a new account**
   - Click on "Register" and create a new patient account

4. **Login**
   - Use your credentials to log in to the system

5. **For Doctors:**
   - View and manage your patients
   - Upload medical records for your patients
   - Request access to patient records from other doctors

6. **For Patients:**
   - View your medical records
   - Manage access permissions for doctors
   - Upload your own medical records

## Configuration Details

### Environment Variables (.env)

The `backend/.env` file contains all configuration settings:

```dotenv
# Django Settings
DJANGO_SECRET_KEY=dev-secret-key-change-in-production-...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=medical_secure
DB_USER=medical_user
DB_PASSWORD=secure123
DB_HOST=localhost
DB_PORT=5432

# Keycloak Configuration
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=medical-realm
KEYCLOAK_CLIENT_ID=medical-app
KEYCLOAK_CLIENT_SECRET=WTpUYIN6Vsg6QeRWwm6H7k6pPLDq9fXw
```

Note: In a production environment, the .env file should be added to .gitignore and managed securely.

### Finding Keycloak Client Secret

If you need to retrieve or regenerate the Keycloak client secret:

1. Access Keycloak Admin Console at http://localhost:8080
2. Login with `admin` / `admin123`
3. Select the `medical-realm` realm (top-left dropdown)
4. Navigate to **Clients** in the left menu
5. Click on `medical-app`
6. Go to the **Credentials** tab
7. The **Client Secret** is displayed there

> **Note**: The default client secret is already configured in `.env` from the imported realm configuration.

5. **For Patients:**
   - View your medical records
   - Manage access permissions for doctors
   - Upload your own medical records




### Database Connection Issues
- Ensure Docker services are running: `docker ps`
- Check if PostgreSQL is accessible: `docker logs medical-postgres`
- Verify database credentials in `backend/.env`

### Keycloak Issues
- Check if Keycloak is running: `docker ps | grep keycloak`
- Access logs: `docker logs medical-keycloak`
- Verify Keycloak URL in `.env` matches: `http://localhost:8080`

### Migrations Not Applied
If you see "unapplied migrations" warning:
```bash
cd backend
python manage.py migrate
```

### Module Not Found Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt` and `npm install`
- For Python: check if you're in the correct directory (`backend/`)
- For Node.js: check if you're in the correct directory (`frontend/`)

### Port Already in Use
If ports 5432, 8000, 8080, or 5173 are already in use:
- Check running processes: `netstat -ano | findstr "8000"` (Windows) or `lsof -i :8000` (Ubuntu)
- Stop conflicting services or change ports in configuration files
