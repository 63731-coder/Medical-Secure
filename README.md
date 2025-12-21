# SecureMed - Secure Medical Records Management System

## Group Members
- **Nicoleta OPRE** - Matricule: 63731
- **Abla NEGUE** - Matricule: 60991
- **Adam MOUSSA** - Matricule: 62755
- **Christophe ANTAR** - Matricule: 62642
- **Damian WESOLOWSKI** - Matricule: 62834

## Project Description
SecureMed is a secure medical records management system with end-to-end encryption. It allows patients to upload encrypted medical files and share them with appointed doctors. The system uses Keycloak for authentication and authorization.

## Technologies
- **Frontend**: Vue.js 3 + Vite
- **Backend**: Django 5.2.8 + Django REST Framework
- **Authentication**: Keycloak 23.0.7 (OAuth2/OIDC)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Encryption**: Client-side AES-256 encryption with CryptoJS

---

## Build Instructions

### Prerequisites

#### For Ubuntu 22.04 x64:
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Node.js 18+ and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Docker and Docker Compose
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### For Windows 10 x64:
1. **Install Python 3.10+**: Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation
2. **Install Node.js 18+**: Download from https://nodejs.org/
3. **Install Docker Desktop**: Download from https://www.docker.com/products/docker-desktop/
   - Start Docker Desktop after installation

---

### Automated Installation (Recommended)

#### For Ubuntu 22.04 x64:

**Option 1: Using the setup script**
```bash
chmod +x setup.sh
./setup.sh
```

**Option 2: Using Makefile**
```bash
make install
```

The script will automatically:
- Create Python virtual environment
- Install all Python dependencies
- Install Node.js dependencies
- Create .env configuration file
- Run database migrations
- Start Keycloak with Docker

#### For Windows 10 x64:

**Run the setup script:**
```cmd
setup.bat
```

The script will automatically:
- Create Python virtual environment
- Install all Python dependencies
- Install Node.js dependencies
- Create .env configuration file
- Run database migrations
- Start Keycloak with Docker

After installation, use these commands to start the application:
- **Backend**: `start-backend.bat`
- **Frontend**: `start-frontend.bat`

---

### Manual Installation Steps

#### 1. Clone the Repository
```bash
git clone https://git.esi-bru.be/2025-2026/5prj2d/e112/team-b/security-prj.git
cd security-prj
```

#### 2. Backend Setup

##### Ubuntu:
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DJANGO_SECRET_KEY=your-secret-key-here
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=medical-realm
KEYCLOAK_CLIENT_ID=medical-app
KEYCLOAK_CLIENT_SECRET=OESLG5iTt2FSRegpLhgRRTvKY7eugLpt
KEYCLOAK_REDIRECT_URI=http://localhost:5173/callback
EOF

# Run migrations
python manage.py migrate

# Return to project root
cd ..
```

##### Windows:
```cmd
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file manually with the following content:
# DJANGO_SECRET_KEY=your-secret-key-here
# KEYCLOAK_SERVER_URL=http://localhost:8080
# KEYCLOAK_REALM=medical-realm
# KEYCLOAK_CLIENT_ID=medical-app
# KEYCLOAK_CLIENT_SECRET=OESLG5iTt2FSRegpLhgRRTvKY7eugLpt
# KEYCLOAK_REDIRECT_URI=http://localhost:5173/callback

# Run migrations
python manage.py migrate

# Return to project root
cd ..
```

#### 3. Frontend Setup

##### Ubuntu:
```bash
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

##### Windows:
```cmd
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

#### 4. Keycloak Setup (Both Ubuntu and Windows)
```bash
# Start Keycloak and PostgreSQL using Docker Compose
docker-compose up -d

# Wait for Keycloak to start (about 30-60 seconds)
# Verify it's running at http://localhost:8080
```

**Important**: The Keycloak realm configuration is automatically imported from `keycloak-import/medical-realm.json` when the container starts. This includes:
- Realm: `medical-realm`
- Client: `medical-app`
- Roles: `patient` and `doctor`
- Admin credentials: `admin` / `admin123`

---

## Usage Instructions

### Quick Start

#### For Ubuntu 22.04 x64:

**Using Makefile (Recommended):**
```bash
# In Terminal 1:
make start-backend

# In Terminal 2:
make start-frontend
```

**Or manually:**
```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
python manage.py runserver

# Terminal 2: Start frontend
cd frontend
npm run dev
```

#### For Windows 10 x64:

**Using batch scripts (Recommended):**
```cmd
# In Terminal 1:
start-backend.bat

# In Terminal 2:
start-frontend.bat
```

**Or manually:**
```cmd
# Terminal 1: Start backend
cd backend
venv\Scripts\activate
python manage.py runserver

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### Access Points
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **Keycloak Admin Console**: http://localhost:8080 (admin/admin123)

---

### Using the Application

1. **Access the Application**: Open your browser and navigate to http://localhost:5173

2. **Register a New Account**:
   - Click on "Register"
   - Fill in the registration form (username, email, password, first name, last name, date of birth)
   - Select account type: Patient or Doctor
   - Submit the form

3. **Login**:
   - You will be redirected to Keycloak login page
   - Enter your credentials
   - After successful login, you'll be redirected back to the application

4. **Patient Features**:
   - Upload encrypted medical files
   - View and download your medical records
   - Search for doctors
   - Send appointment requests to doctors
   - Manage appointed doctors

5. **Doctor Features**:
   - View patient requests
   - Access medical files of appointed patients
   - Approve/deny file access requests
   - View list of all patients under care

---

## Synchronizing User Data from Keycloak

If user profile information is not displaying correctly, run the synchronization script:

##### Ubuntu:
```bash
cd backend
source venv/bin/activate
python sync_users.py
```

##### Windows:
```cmd
cd backend
venv\Scripts\activate
python sync_users.py
```

This script fetches user information from Keycloak and updates the Django database.

---

## Stopping the Application

1. Stop Frontend: Press `Ctrl+C` in Terminal 3
2. Stop Backend: Press `Ctrl+C` in Terminal 2
3. Stop Keycloak:
   ```bash
   docker-compose down
   ```

---

## API Endpoints

### Authentication
- `POST /api/auth/keycloak/register/` - Register new user
- `POST /api/auth/keycloak/callback/` - OAuth2 callback
- `POST /api/auth/keycloak/refresh/` - Refresh access token
- `POST /api/auth/keycloak/logout/` - Logout user
- `GET /api/auth/me/` - Get current user profile

### Medical Files
- `GET /api/files/` - List user's medical files
- `POST /api/files/` - Upload encrypted file
- `GET /api/files/{id}/download/` - Download encrypted file
- `DELETE /api/files/{id}/` - Delete file

### Doctors & Patients
- `GET /api/doctors/` - List all doctors
- `GET /api/patients/` - List current user's patients (for doctors)
- `POST /api/patients/{id}/add-doctor/` - Appoint a doctor
- `DELETE /api/patients/{id}/remove-doctor/{doctor_id}/` - Remove doctor

### Requests
- `GET /api/doctor-requests/` - List doctor appointment requests
- `POST /api/doctor-requests/` - Create appointment request
- `PATCH /api/doctor-requests/{id}/` - Approve/deny request
- `GET /api/file-requests/` - List file access requests
- `POST /api/file-requests/` - Create file access request
- `PATCH /api/file-requests/{id}/` - Approve/deny file access

---

## Troubleshooting

### Issue: Keycloak not accessible
- Ensure Docker is running
- Wait 30-60 seconds after `docker-compose up` for Keycloak to fully start
- Check logs: `docker-compose logs keycloak`

### Issue: Profile shows "N/A" for user information
- Run the sync script: `python sync_users.py`
- Ensure user information is filled in Keycloak admin console

### Issue: Database errors
- Delete `backend/db.sqlite3` and run `python manage.py migrate` again

### Issue: Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/config/settings.py`

---

## Project Structure
```
security-prj/
├── backend/                    # Django backend
│   ├── config/                # Django settings
│   ├── med_secure/            # Main application
│   │   ├── management/        # Custom management commands
│   │   ├── migrations/        # Database migrations
│   │   ├── models.py          # Database models
│   │   ├── views.py           # API views
│   │   ├── keycloak_auth.py   # Keycloak JWT authentication
│   │   └── keycloak_views.py  # Keycloak OAuth2 views
│   ├── media/                 # Encrypted file storage
│   ├── manage.py              # Django management script
│   ├── sync_users.py          # Keycloak sync script
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Vue.js frontend
│   ├── src/
│   │   ├── components/        # Vue components
│   │   ├── views/             # Page views
│   │   ├── services/          # API services
│   │   ├── utils/             # Utilities (encryption)
│   │   └── router/            # Vue Router
│   └── package.json           # NPM dependencies
├── keycloak-import/           # Keycloak realm configuration
│   └── medical-realm.json
└── docker-compose.yml         # Docker services configuration
```

---

## Security Features
- End-to-end encryption using AES-256
- OAuth2/OIDC authentication via Keycloak
- JWT token-based API authentication
- Role-based access control (Patient/Doctor)
- Request approval system for doctor appointments
- File access request system with approval workflow
- Input sanitization and validation
- CORS protection

---

## License
This project is developed as part of the Security course at HE2B ESI (2025-2026).



## Getting started

To make it easy for you to get started with GitLab, here's a list of recommended next steps.

Already a pro? Just edit this README.md and make it your own. Want to make it easy? [Use the template at the bottom](#editing-this-readme)!

## Add your files

- [ ] [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
- [ ] [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd existing_repo
git remote add origin https://git.esi-bru.be/2025-2026/5prj2d/e112/team-b/security-prj.git
git branch -M main
git push -uf origin main
```

## Integrate with your tools

- [ ] [Set up project integrations](https://git.esi-bru.be/2025-2026/5prj2d/e112/team-b/security-prj/-/settings/integrations)

## Collaborate with your team

- [ ] [Invite team members and collaborators](https://docs.gitlab.com/ee/user/project/members/)
- [ ] [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
- [ ] [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
- [ ] [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)
- [ ] [Set auto-merge](https://docs.gitlab.com/ee/user/project/merge_requests/merge_when_pipeline_succeeds.html)

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/ee/user/application_security/sast/)
- [ ] [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/ee/topics/autodevops/requirements.html)
- [ ] [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/ee/user/clusters/agent/)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

# Editing this README

When you're ready to make this README your own, just edit this file and use the handy template below (or feel free to structure it however you want - this is just a starting point!). Thanks to [makeareadme.com](https://www.makeareadme.com/) for this template.

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
