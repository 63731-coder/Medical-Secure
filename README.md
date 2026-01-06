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

## Getting Started

You have three options to setup and run the application:
1. **Automated Setup with HTTPS** (Recommended for production-like testing) - Using TLS/SSL
2. **Automated Setup** (Quick start for development) - Using HTTP scripts
3. **Manual Setup** - Using terminal commands

---

## Option 1: Automated Setup with HTTPS/TLS (Recommended)

This option starts the application with **TLS/SSL encryption** using nginx as a reverse proxy, providing a production-like secure environment.

### Step 1: Generate SSL Certificates

The SSL certificates are automatically generated when you first run the start script. However, if you want to generate them manually:

**On Windows:**
```cmd
cd certs
generate-certs.bat
```

**On Ubuntu:**
```bash
cd certs
chmod +x generate-certs.sh
./generate-certs.sh
```

### Step 2: Start with HTTPS

**On Windows:**
```cmd
start-https.bat
```

**On Ubuntu:**
```bash
chmod +x start-https.sh
./start-https.sh
```

The script will automatically:
- ✅ Generate SSL certificates (if not already present)
- ✅ Build and start all Docker services (PostgreSQL, Keycloak, Backend, Frontend, Nginx)
- ✅ Configure nginx as reverse proxy with TLS/SSL
- ✅ Apply database migrations
- ✅ Setup secure HTTPS connections

### Access the Application (HTTPS)

Once the script finishes, open your browser:
- **Frontend**: https://localhost (Main application)
- **Backend API**: https://localhost/api
- **Django Admin**: https://localhost/admin
- **Keycloak**: https://localhost/auth
- **Kibana**: https://localhost:5601

⚠️ **Important**: Your browser will show a security warning because the SSL certificate is self-signed for development. Click "Advanced" and "Proceed to localhost" to accept the certificate.

---

## Option 2: Automated Setup (HTTP)

This is the easiest way to get started. We provide automated scripts that handle everything for you.

### Step 1: Run Setup Script

**On Windows:**
```cmd
setup.bat
```

**On Ubuntu:**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will automatically:
- ✅ Check if Docker, Python, and Node.js are installed
- ✅ Start Docker services (PostgreSQL, Keycloak)
- ✅ Install Python packages
- ✅ Run database migrations
- ✅ Install Node.js packages

### Step 2: Run the Application

**On Windows:**
```cmd
run.bat
```

**On Ubuntu:**
```bash
./run.sh
```

The run script will automatically:
- ✅ Start Docker services (if not already running)
- ✅ Launch the backend server on port 8000 (in a new window)
- ✅ Launch the frontend server on port 5173 (in a new window)

### Access the Application

Once the scripts finish, open your browser:
- **Frontend**: http://localhost:5173
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)

---

## Option 3: Manual Setup

If you prefer to run commands manually, follow these steps:

### Step 1: Install Dependencies

**Install Docker and Docker Compose:**
- Ubuntu: `sudo apt-get install docker.io docker-compose`
- Windows: Install Docker Desktop from https://www.docker.com/products/docker-desktop

### Step 2: Start Docker Services

```bash
docker-compose up -d
```

Wait ~10 seconds for services to be ready (PostgreSQL, Keycloak).

> **Note**: The `backend/.env` file is already included in the repository with all necessary configuration (Django settings, database credentials, Keycloak configuration).

### Step 3: Setup Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
```

### Step 4: Setup Frontend

```bash
cd frontend
npm install
```

### Step 5: Start Backend Server

Open a terminal and run:

**On Ubuntu:**
```bash
cd backend
python3 manage.py runserver 0.0.0.0:8000
```

**On Windows:**
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```


### Step 6: Start Frontend Server

Open another terminal and run:

```bash
cd frontend
npm run dev
```

The frontend application will be available at http://localhost:5173

### Access the Application

- **Frontend**: http://localhost:5173
- **Keycloak Admin**: http://localhost:8080 (admin/admin123)

## Usage

1. **Access the application**
   - Open your web browser and navigate to http://localhost:5173

2. **Access Keycloak Admin Console** (if needed)
   - URL: http://localhost:8080
   - Username: `admin`
   - Password: `admin123`
   - The `medical-realm` is automatically imported with pre-configured users and roles

3. **Register a new account**
   - Click on "Create Account" and create a new patient account

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

# Google reCAPTCHA Configuration (for bot protection)
RECAPTCHA_SECRET_KEY=6Lfb-T8sAAAAAGIJwbF7Zh-6a0u-ExsozUXyfpD2
```

**Note**: In a production environment, the .env file should be added to .gitignore and managed securely.

### Google reCAPTCHA Setup

The registration page uses **Google reCAPTCHA v3** (invisible) to prevent bot attacks. To configure:

1. **Create a free reCAPTCHA account** at https://www.google.com/recaptcha/admin/create
2. **Register a new site**:
   - Label: `MedSecure App` (or any name)
   - reCAPTCHA type: **v3** (invisible, no challenge)
   - Domain: `localhost` (for development, just the hostname without protocol or port)
3. **Copy your keys**:
   - **Site key**: Copy and paste into [frontend/src/main.js](frontend/src/main.js) (replace the siteKey value in VueReCaptcha config)
   - **Secret key**: Add to `backend/.env` as `RECAPTCHA_SECRET_KEY`
4. **Restart both frontend and backend** to apply changes

> **Important**: The reCAPTCHA v3 is invisible - users won't see any checkbox or image challenge. It works automatically in the background to detect bots.

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

---

## TLS/SSL Configuration

The application implements **TLS 1.2 and TLS 1.3** encryption for all communications through nginx reverse proxy.

### Architecture

```
Client Browser (HTTPS)
    ↓ TLS/SSL
Nginx Reverse Proxy (Port 443)
    ↓ HTTP (internal Docker network)
    ├─→ Frontend (Vue.js) - Port 5173
    ├─→ Backend (Django) - Port 8000
    └─→ Keycloak - Port 8080
```

### Security Features

1. **SSL/TLS Configuration**:
   - TLS 1.2 and TLS 1.3 protocols
   - Strong cipher suites (ECDHE, AES-GCM, ChaCha20-Poly1305)
   - Perfect Forward Secrecy (PFS)
   - Session caching for performance

2. **Security Headers**:
   - `Strict-Transport-Security` (HSTS) - Force HTTPS for 1 year
   - `X-Frame-Options` - Prevent clickjacking
   - `X-Content-Type-Options` - Prevent MIME sniffing
   - `X-XSS-Protection` - XSS filter enabled
   - `Content-Security-Policy` - Control resource loading
   - `Referrer-Policy` - Control referrer information

3. **Automatic HTTP to HTTPS Redirection**:
   - All HTTP (port 80) traffic is automatically redirected to HTTPS (port 443)

### Certificate Management

For **development**, self-signed certificates are used:
- Generated automatically by `generate-certs.sh` or `generate-certs.bat`
- Valid for 365 days
- Include SAN (Subject Alternative Names) for localhost and 127.0.0.1

For **production**, use certificates from:
- **Let's Encrypt** (free, recommended) - https://letsencrypt.org/
- A trusted Certificate Authority (CA)

### Nginx Configuration

The nginx configuration ([nginx/nginx.conf](nginx/nginx.conf)) includes:
- Reverse proxy for frontend, backend, and Keycloak
- TLS termination
- Security headers
- Request size limits (100MB for file uploads)
- Health check endpoint at `/health`

---

## Security Note

> **⚠️ Important - Security Best Practice:**  
> For educational purposes, the `.env` file containing configuration secrets is included in this repository to simplify setup and evaluation. **In a professional/production environment, you should NEVER commit `.env` files to version control!** Always use `.gitignore` to exclude them and provide a `.env.example` template instead.

## Security Checklist Report

> **📋 Security Documentation:**  
> A comprehensive security checklist report covering all 15 security points is available in the `/rapports` folder:
>`Security_Checklist_Report.md`
>
> This report detail how each security measure is implemented in our project, with code examples and explanations.
