@echo off
REM Script de test pour vérifier la configuration TLS

echo 🔍 Test de la configuration TLS/HTTPS
echo =====================================
echo.

REM 1. Vérifier que les certificats existent
echo 1. Vérification des certificats...
if exist ".\certs\localhost.key" if exist ".\certs\localhost.crt" (
    echo ✓ Certificats SSL trouvés
    echo.
    echo Détails du certificat:
    openssl x509 -in .\certs\localhost.crt -text -noout | findstr "Subject:"
    openssl x509 -in .\certs\localhost.crt -text -noout | findstr "Not After"
    echo.
) else (
    echo ✗ Certificats SSL manquants
    echo    Exécutez: cd certs ^&^& generate-certs.bat
    pause
    exit /b 1
)

REM 2. Vérifier que Docker est en cours d'exécution
echo 2. Vérification de Docker...
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker est actif
) else (
    echo ✗ Docker n'est pas actif
)

REM 3. Vérifier que les conteneurs sont en cours d'exécution
echo.
echo 3. Vérification des conteneurs...
for %%c in (medical-nginx medical-backend medical-frontend medical-keycloak medical-postgres) do (
    docker ps --format "{{.Names}}" | findstr /x "%%c" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✓ %%c est actif
    ) else (
        echo ⚠ %%c n'est pas actif
    )
)

REM 4. Tester la connexion HTTPS
echo.
echo 4. Test de connexion HTTPS...
curl -k -s -f https://localhost/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Nginx répond ^(health check^)
) else (
    echo ✗ Nginx ne répond pas
)

REM 5. Tester les protocoles TLS
echo.
echo 5. Test des protocoles TLS...

echo | openssl s_client -connect localhost:443 -tls1_2 2>&1 | findstr "Protocol.*TLSv1.2" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ TLS 1.2 supporté
) else (
    echo ⚠ TLS 1.2 non détecté
)

echo | openssl s_client -connect localhost:443 -tls1_3 2>&1 | findstr "Protocol.*TLSv1.3" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ TLS 1.3 supporté
) else (
    echo ⚠ TLS 1.3 non détecté
)

REM 6. Tester les headers de sécurité
echo.
echo 6. Test des headers de sécurité...

curl -k -s -I https://localhost/ | findstr "Strict-Transport-Security" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ HSTS header présent
) else (
    echo ⚠ HSTS header manquant
)

curl -k -s -I https://localhost/ | findstr "X-Frame-Options" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ X-Frame-Options présent
) else (
    echo ⚠ X-Frame-Options manquant
)

curl -k -s -I https://localhost/ | findstr "X-Content-Type-Options" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ X-Content-Type-Options présent
) else (
    echo ⚠ X-Content-Type-Options manquant
)

REM 7. Tester la redirection HTTP -> HTTPS
echo.
echo 7. Test de la redirection HTTP -^> HTTPS...
curl -s -I http://localhost/ | findstr /C:"301" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Redirection HTTP -^> HTTPS active
) else (
    echo ⚠ Redirection HTTP -^> HTTPS non détectée
)

REM 8. Résumé
echo.
echo =====================================
echo 📊 Résumé des tests
echo =====================================
echo.
echo URLs à tester dans le navigateur:
echo   • https://localhost
echo   • https://localhost/api
echo   • https://localhost/auth
echo.
echo ⚠️  N'oubliez pas d'accepter le certificat auto-signé dans votre navigateur!
echo.
pause
