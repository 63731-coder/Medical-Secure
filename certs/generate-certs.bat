@echo off
REM Script pour générer des certificats SSL auto-signés pour localhost (Windows)
REM Pour le développement uniquement

setlocal enabledelayedexpansion
set CERTS_DIR=%~dp0
set DAYS_VALID=365

echo 🔐 Génération des certificats SSL auto-signés pour localhost...
echo.

REM Vérifier si OpenSSL est disponible
where openssl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ OpenSSL n'est pas installé ou n'est pas dans le PATH.
    echo.
    echo 💡 Utilisation de Docker à la place...
    echo.
    call "%~dp0generate-certs-docker.bat"
    exit /b %ERRORLEVEL%
)

REM Supprimer les anciens certificats s'ils existent
if exist "%CERTS_DIR%localhost.key" del /f /q "%CERTS_DIR%localhost.key"
if exist "%CERTS_DIR%localhost.crt" del /f /q "%CERTS_DIR%localhost.crt"
if exist "%CERTS_DIR%localhost.csr" del /f /q "%CERTS_DIR%localhost.csr"

REM Générer la clé privée
echo 📝 Génération de la clé privée...
openssl genrsa -out "%CERTS_DIR%localhost.key" 2048
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de la génération de la clé privée
    pause
    exit /b 1
)

REM Créer un fichier de configuration pour le certificat
echo 📝 Création du fichier de configuration...
(
echo [req]
echo default_bits = 2048
echo prompt = no
echo default_md = sha256
echo distinguished_name = dn
echo x509_extensions = v3_req
echo.
echo [dn]
echo C = BE
echo ST = Belgium
echo L = Brussels
echo O = Medical Secure
echo OU = Development
echo CN = localhost
echo.
echo [v3_req]
echo subjectAltName = @alt_names
echo basicConstraints = CA:FALSE
echo keyUsage = nonRepudiation, digitalSignature, keyEncipherment
echo extendedKeyUsage = serverAuth
echo.
echo [alt_names]
echo DNS.1 = localhost
echo DNS.2 = *.localhost
echo IP.1 = 127.0.0.1
echo IP.2 = ::1
) > "%CERTS_DIR%openssl.cnf"

REM Générer le certificat auto-signé
echo 📜 Génération du certificat auto-signé...
openssl req -new -x509 -key "%CERTS_DIR%localhost.key" -out "%CERTS_DIR%localhost.crt" -days %DAYS_VALID% -config "%CERTS_DIR%openssl.cnf"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de la génération du certificat
    del /f /q "%CERTS_DIR%openssl.cnf"
    pause
    exit /b 1
)

REM Nettoyer le fichier de configuration temporaire
del /f /q "%CERTS_DIR%openssl.cnf"

REM Vérifier que les fichiers ont été créés
if exist "%CERTS_DIR%localhost.key" if exist "%CERTS_DIR%localhost.crt" (
    echo.
    echo ✅ Certificats générés avec succès!
    echo.
    echo 📁 Fichiers créés:
    echo    - %CERTS_DIR%localhost.key ^(Clé privée^)
    echo    - %CERTS_DIR%localhost.crt ^(Certificat^)
    echo.
    echo ⚠️  IMPORTANT: Ces certificats sont auto-signés et destinés au développement uniquement.
    echo     Votre navigateur affichera un avertissement de sécurité. Vous devrez accepter le risque.
    echo.
    echo 🔍 Pour voir les détails du certificat:
    echo     openssl x509 -in "%CERTS_DIR%localhost.crt" -text -noout
    echo.
) else (
    echo ❌ Erreur lors de la génération des certificats
    pause
    exit /b 1
)

pause
