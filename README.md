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

The application uses a secure containerized architecture with nginx as reverse proxy:

```
Client Browser (HTTPS)
    ↓ TLS 1.2/1.3
Nginx Reverse Proxy (Port 443/80)
    ↓ HTTP (internal Docker network - secure)
    ├─→ Frontend (Vue.js) - Container: medical-frontend
    ├─→ Backend (Django) - Container: medical-backend
    ├─→ Keycloak (Auth) - Container: medical-keycloak
    └─→ ELK Stack (Logs) - Containers: elasticsearch, logstash, kibana
```

**Security Model:**
- All external traffic is encrypted with TLS 1.2/1.3
- Internal services communicate within isolated Docker network
- Only nginx port 443 (HTTPS) and 80 (HTTP→HTTPS redirect) are exposed
- Backend, frontend, and Keycloak are NOT directly accessible from outside

**Components:**

1. **Nginx Reverse Proxy**
   - TLS termination with modern cipher suites
   - Security headers (HSTS, CSP, X-Frame-Options, etc.)
   - Routes traffic to internal services
   - Automatic HTTP to HTTPS redirection

2. **Backend (Django REST API)**
   - Handles business logic and data management
   - End-to-end encryption for medical records
   - Keycloak integration for authentication
   - PostgreSQL database connection

3. **Frontend (Vue.js SPA)**
   - Modern single-page application
   - Client-side encryption/decryption of medical data
   - Keycloak OAuth2/OIDC authentication flow

4. **Authentication (Keycloak)**
   - Identity and access management
   - Pre-configured realm with HTTPS redirect URIs
   - OAuth 2.0 / OpenID Connect
   - Passwordless authentication support

5. **Database (PostgreSQL x2)**
   - medical-postgres: Application data (encrypted medical records)
   - keycloak-postgres: Keycloak user data

6. **ELK Stack (Monitoring)**
   - Elasticsearch: Log storage and indexing
   - Logstash: Log processing and enrichment
   - Kibana: Log visualization and analysis

## Prerequisites

- **Docker Desktop** (Windows) or **Docker + Docker Compose** (Linux/Mac)
- That's it! Everything else runs in containers.

**Tested on:**
- Windows 10/11 (x64)
- Ubuntu 22.04 (x64)

**Note:** Python, Node.js, PostgreSQL, and Keycloak are NOT required on your host machine - they run inside Docker containers.

## Getting Started

### 🚀 Quick Start (Recommended)

The application runs with **full TLS/HTTPS encryption** using nginx as a reverse proxy. Everything is containerized with Docker for easy deployment.

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
The script will automatically:
- ✅ Generate SSL certificates (if not already present)
- ✅ Build and start all Docker services
- ✅ Configure nginx reverse proxy with TLS 1.2/1.3
- ✅ Setup all services in Docker network
- ✅ Display service status

**⚠️ Important - Database Migrations:**
After starting the services for the first time, you need to apply Django migrations:
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 🌐 Access the Application

Once the script finishes, open your browser:
- **Frontend**: https://localhost (Main application)
- **Django Admin**: https://localhost/admin
- **Keycloak Admin**: https://localhost/auth/admin (admin/admin123)
- **Kibana (Logs)**: https://localhost:5601

⚠️ **Important**: Your browser will show a security warning because the SSL certificate is self-signed for development. Click "Advanced" and "Proceed to localhost" to accept the certificate.

### 🛑 Stop the Application

```cmd
docker-compose down
```

### 🔄 Restart with New Configuration

If you or your teammates clone the project from Git:

```cmd
start-https.bat
```

All configuration (Keycloak realm, HTTPS URLs, security settings) is automatically loaded from the repository files:
- `keycloak-import/medical-realm.json` - Pre-configured Keycloak with HTTPS redirect URIs
- `docker-compose.yml` - All environment variables and service configuration
- `nginx/nginx.conf` - Reverse proxy with TLS configuration

### 🔧 Troubleshooting Certificate Issues

If certificates are corrupted (showing as directories instead of files):

```cmd
cd certs
rmdir /s /q localhost.crt localhost.key 2>nul
del /q openssl.cnf localhost.csr 2>nul
cd ..
start-https.bat
```

### 🔑 Reset Keycloak Configuration

If Keycloak has old configuration (wrong redirect URIs):

```cmd
reset-keycloak.bat
```

This will delete the Keycloak database and reimport the latest configuration from `keycloak-import/medical-realm.json`.

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

### Environment Variables

All configuration is managed through Docker Compose and environment variables. The main configurations are:

**Backend Configuration** (in `docker-compose.yml`):
```yaml
environment:
  DJANGO_SECRET_KEY: dev-secret-key-change-in-production
  DEBUG: "True"
  ALLOWED_HOSTS: localhost,127.0.0.1,backend
  KEYCLOAK_SERVER_URL: http://keycloak:8080  # Internal URL
  KEYCLOAK_PUBLIC_URL: https://localhost/auth  # External URL via nginx
  KEYCLOAK_REALM: medical-realm
  KEYCLOAK_CLIENT_ID: medical-app
  RECAPTCHA_SECRET_KEY: 6Lfb-T8sAAAAAGIJwbF7Zh-6a0u-ExsozUXyfpD2
```

**Frontend Configuration** (in `docker-compose.yml`):
```yaml
environment:
  VITE_API_URL: https://localhost/api  # API accessible via nginx
```

**Keycloak Configuration** (in `docker-compose.yml`):
```yaml
environment:
  KC_HOSTNAME_URL: https://localhost/auth  # Public URL
  KC_PROXY: edge  # Behind reverse proxy
  KEYCLOAK_ADMIN: admin
  KEYCLOAK_ADMIN_PASSWORD: admin123
```

### Keycloak Realm Import

The Keycloak realm configuration is automatically imported from `keycloak-import/medical-realm.json`:
- Pre-configured client: `medical-app`
- Client secret: `WTpUYIN6Vsg6QeRWwm6H7k6pPLDq9fXw`
- Redirect URIs: `https://localhost/*`, `https://localhost/callback`
- Web origins: `https://localhost`

**When teammates clone the repository:** All Keycloak settings are already configured correctly for HTTPS!

### Google reCAPTCHA Setup

The registration page uses **Google reCAPTCHA v3** (invisible) to prevent bot attacks. The default keys are configured for localhost testing.

**To use your own reCAPTCHA keys:**

1. **Create a free reCAPTCHA account** at https://www.google.com/recaptcha/admin/create
2. **Register a new site**:
   - Label: `MedSecure App`
   - reCAPTCHA type: **v3** (invisible)
   - Domain: `localhost`
3. **Update the keys**:
   - **Site key**: Update in `frontend/src/main.js` (VueReCaptcha config)
   - **Secret key**: Update `RECAPTCHA_SECRET_KEY` in `docker-compose.yml` backend environment
4. **Rebuild containers**: `docker-compose up --build -d`

> **Note**: reCAPTCHA v3 is invisible - no checkbox or image challenge appears. It analyzes user behavior to detect bots.

### Finding Keycloak Client Secret

The client secret is pre-configured in `keycloak-import/medical-realm.json`. To view or change it:

1. Access Keycloak Admin at https://localhost/auth/admin
2. Login: `admin` / `admin123`
3. Select `medical-realm` (top-left dropdown)
4. Go to **Clients** → `medical-app` → **Credentials** tab
5. View/regenerate the client secret

If you change it in Keycloak UI, update it in:
- `keycloak-import/medical-realm.json` (to persist for teammates)
- `docker-compose.yml` backend environment (optional, not currently used)

## Troubleshooting

### Container Issues
- **Check running containers**: `docker-compose ps`
- **View container logs**: `docker-compose logs -f [service-name]`
  - Services: `nginx`, `backend`, `frontend`, `keycloak`, `postgres`, `keycloak-db`
- **Restart all services**: `docker-compose restart`
- **Rebuild containers**: `docker-compose up --build -d`

### Certificate Issues
If certificates show as directories instead of files:
```cmd
cd certs
rmdir /s /q localhost.crt localhost.key 2>nul
del /q openssl.cnf 2>nul
cd ..
start-https.bat
```

### Keycloak Redirect URI Errors
If you see "Invalid parameter: redirect_uri":
```cmd
reset-keycloak.bat
```
This reimports the Keycloak configuration with correct HTTPS URIs.

### Port Conflicts
If Docker fails to start due to port conflicts:
- Check what's using ports: `netstat -ano | findstr "443 80 8080 5432 5173 8000"`
- Stop the conflicting service or change ports in `docker-compose.yml`

### Browser Shows "NET::ERR_CERT_AUTHORITY_INVALID"
This is normal for self-signed certificates:
1. Click **Advanced**
2. Click **Proceed to localhost (unsafe)**
3. The certificate is valid for development only

### Database Connection Issues
- Ensure PostgreSQL containers are running: `docker ps | findstr postgres`
- Check logs: `docker-compose logs postgres`
- Verify database is initialized: `docker-compose exec backend python manage.py migrate`

### Frontend Can't Connect to Backend
- Verify nginx is running: `docker ps | findstr nginx`
- Check nginx logs: `docker-compose logs nginx`
- Ensure you're accessing via HTTPS: `https://localhost` (not http://localhost:5173)
- Clear browser cache: `Ctrl+Shift+R`

---

## TLS/SSL Configuration

The application implements **TLS 1.2 and TLS 1.3** encryption for all external communications through nginx reverse proxy.

### Security Architecture

```
Internet/Browser (HTTPS - Encrypted)
    ↓ TLS 1.2/1.3
Nginx Reverse Proxy (Port 443)
    ↓ HTTP (Internal Docker Network - Isolated & Secure)
    ├─→ Frontend (Vue.js)
    ├─→ Backend (Django API)
    └─→ Keycloak (Authentication)
```

**Why this design?**
- TLS termination at nginx reduces complexity and improves performance
- Internal services don't need TLS certificates
- Docker network isolation prevents external access to internal services
- Only nginx port 443 (HTTPS) and 80 (HTTP redirect) are exposed

### Security Features Implemented

1. **TLS/SSL Configuration** ([nginx/nginx.conf](nginx/nginx.conf)):
   - TLS 1.2 and TLS 1.3 protocols only (TLS 1.0/1.1 disabled)
   - Strong cipher suites: ECDHE-RSA-AES256-GCM-SHA384, ECDHE-RSA-AES128-GCM-SHA256, ECDHE-RSA-CHACHA20-POLY1305
   - Perfect Forward Secrecy (PFS) enabled
   - Session caching for performance (10MB cache, 10min timeout)
   - SSL session tickets disabled for security

2. **HTTP Security Headers**:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` - Force HTTPS for 1 year
   - `X-Frame-Options: DENY` - Prevent clickjacking
   - `X-Content-Type-Options: nosniff` - Prevent MIME sniffing
   - `X-XSS-Protection: 1; mode=block` - Enable XSS filter
   - `Content-Security-Policy` - Control resource loading (scripts, styles, images, frames, connections)
   - `Referrer-Policy: strict-origin-when-cross-origin` - Control referrer information

3. **Automatic HTTP to HTTPS Redirection**:
   - All HTTP traffic (port 80) automatically redirects to HTTPS (port 443)
   - 301 permanent redirect for SEO and security

4. **Request Security**:
   - Client body size limit: 100MB (for medical file uploads)
   - Buffer size limits configured
   - Timeouts configured appropriately

### Certificate Management

**Development (Current Setup):**
- Self-signed certificates generated automatically by `generate-certs.bat` or `generate-certs.sh`
- Valid for 365 days
- Subject Alternative Names (SAN) for localhost, 127.0.0.1, ::1
- RSA 2048-bit key
- SHA-256 signature

**Certificate Generation Options:**
1. **OpenSSL** (if installed): `certs/generate-certs.bat` uses local OpenSSL
2. **Docker** (fallback): Uses `alpine/openssl` Docker image if OpenSSL not found
3. **mkcert** (recommended for trusted certs): See `certs/generate-certs-mkcert.bat`

**Production Recommendations:**
- Use **Let's Encrypt** (free, automated renewal): https://letsencrypt.org/
- Or purchase certificate from a trusted Certificate Authority (CA)
- Never use self-signed certificates in production

### Nginx Reverse Proxy Configuration

**Upstream Services** ([nginx/nginx.conf](nginx/nginx.conf)):
- `frontend` → http://frontend:5173 (Vue.js dev server)
- `backend` → http://backend:8000 (Django application)
- `keycloak` → http://keycloak:8080 (Authentication server)

**Routing Rules:**
- `/` → Frontend (Vue.js SPA)
- `/api/*` → Backend API
- `/admin/*` → Django Admin
- `/media/*` → Medical file storage
- `/auth/*` → Keycloak (with URL rewrite /auth → /)
- `/health` → Nginx health check

**Special Keycloak Configuration:**
- Keycloak requires `KC_PROXY=edge` and `KC_HOSTNAME_URL` set to public URL
- Nginx rewrites `/auth/` to `/` before proxying to Keycloak
- WebSocket support enabled for Keycloak admin console

---

## Security Note

> **⚠️ Important - Security Best Practice:**  
> For educational purposes, configuration values are included directly in `docker-compose.yml` and repository files to simplify setup and evaluation. **In a professional/production environment:**
> - Use `.env` files for secrets (excluded from Git with `.gitignore`)
> - Use Docker secrets or environment variable injection
> - Use a secrets management service (HashiCorp Vault, AWS Secrets Manager, etc.)
> - Rotate credentials regularly
> - Never commit secrets to version control

## Security Implementation

> **📋 Comprehensive Security Documentation:**  
> Detailed security reports covering all implemented security measures:
> - **`rapports/Security_Checklist_Report.md`** - Complete security checklist with implementations
> - **`rapports/TLS_Configuration_Documentation.md`** - TLS/HTTPS configuration details
>
> These reports explain:
> - All 15+ security points implemented
> - Code examples and file locations
> - Architecture decisions and justifications
> - Testing procedures and validation

### Key Security Features

1. **Transport Security**: TLS 1.2/1.3, HSTS, perfect forward secrecy
2. **Authentication**: Keycloak OAuth2/OIDC, passwordless authentication support
3. **Data Encryption**: End-to-end encryption for medical records (client-side)
4. **Access Control**: Role-based access (doctors, patients), request-approve workflow
5. **Input Validation**: ReCAPTCHA v3, CSRF protection, input sanitization
6. **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options, etc.
7. **Logging & Monitoring**: ELK stack for security event logging
8. **Network Isolation**: Docker network, services not directly exposed
9. **Audit Trail**: All access to medical records logged
10. **Bot Protection**: Google reCAPTCHA v3 on registration
