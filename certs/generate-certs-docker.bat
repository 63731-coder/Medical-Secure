@echo off
REM Script pour générer des certificats SSL avec Docker (pas besoin d'OpenSSL local)

setlocal enabledelayedexpansion
set CERTS_DIR=%~dp0
set DAYS_VALID=365

echo 🔐 Génération des certificats SSL auto-signés avec Docker...
echo.

REM Vérifier si Docker est disponible
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker n'est pas installé ou n'est pas dans le PATH.
    echo    Veuillez installer Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Supprimer les anciens certificats/dossiers s'ils existent
echo 🧹 Nettoyage des anciens fichiers...
if exist "%CERTS_DIR%localhost.key\" (
    rmdir /s /q "%CERTS_DIR%localhost.key"
    echo    - Dossier localhost.key supprimé
)
if exist "%CERTS_DIR%localhost.crt\" (
    rmdir /s /q "%CERTS_DIR%localhost.crt"
    echo    - Dossier localhost.crt supprimé
)
if exist "%CERTS_DIR%localhost.key" del /f /q "%CERTS_DIR%localhost.key"
if exist "%CERTS_DIR%localhost.crt" del /f /q "%CERTS_DIR%localhost.crt"
if exist "%CERTS_DIR%localhost.csr" del /f /q "%CERTS_DIR%localhost.csr"

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

echo 📜 Génération des certificats avec Docker...
docker run --rm -v "%CERTS_DIR%:/certs" alpine/openssl req -x509 -nodes -days %DAYS_VALID% -newkey rsa:2048 -keyout /certs/localhost.key -out /certs/localhost.crt -config /certs/openssl.cnf

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de la génération des certificats avec Docker
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
) else (
    echo ❌ Erreur lors de la génération des certificats
    pause
    exit /b 1
)
