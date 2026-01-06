@echo off
REM Script pour démarrer l'application avec TLS/HTTPS

echo 🚀 Démarrage de Medical Secure App avec TLS/HTTPS
echo ================================================
echo.

REM Vérifier si les certificats existent
if not exist ".\certs\localhost.key" (
    goto generate_certs
)
if not exist ".\certs\localhost.crt" (
    goto generate_certs
)
goto certs_exist

:generate_certs
echo ⚠️  Certificats SSL non trouvés. Génération en cours...
cd certs
call generate-certs.bat
cd ..
echo.
goto continue

:certs_exist
echo ✅ Certificats SSL trouvés
echo.

:continue
REM Arrêter les conteneurs existants
echo 🛑 Arrêt des conteneurs existants...
docker-compose down
echo.

REM Reconstruire et démarrer les conteneurs
echo 🔨 Construction et démarrage des conteneurs...
docker-compose up --build -d
echo.

REM Attendre que les services soient prêts
echo ⏳ Attente du démarrage des services...
timeout /t 10 /nobreak >nul
echo.

REM Vérifier l'état des services
echo 📊 État des services:
docker-compose ps
echo.

REM Afficher les informations de connexion
echo ================================================
echo ✅ Application démarrée avec succès!
echo.
echo 🔗 URLs d'accès (HTTPS^):
echo    - Application: https://localhost
echo    - Backend API: https://localhost/api
echo    - Django Admin: https://localhost/admin
echo    - Keycloak: https://localhost/auth
echo    - Kibana (ELK^): https://localhost:5601
echo.
echo ⚠️  IMPORTANT:
echo    Votre navigateur affichera un avertissement de sécurité car
echo    les certificats sont auto-signés. Vous devez accepter le risque.
echo.
echo 📝 Pour voir les logs:
echo    docker-compose logs -f
echo.
echo 🛑 Pour arrêter l'application:
echo    docker-compose down
echo ================================================
echo.
pause
