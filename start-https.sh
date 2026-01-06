#!/bin/bash

# Script pour démarrer l'application avec TLS/HTTPS

echo "🚀 Démarrage de Medical Secure App avec TLS/HTTPS"
echo "================================================"
echo ""

# Vérifier si les certificats existent
if [ ! -f "./certs/localhost.key" ] || [ ! -f "./certs/localhost.crt" ]; then
    echo "⚠️  Certificats SSL non trouvés. Génération en cours..."
    cd certs
    ./generate-certs.sh
    cd ..
    echo ""
else
    echo "✅ Certificats SSL trouvés"
    echo ""
fi

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose down
echo ""

# Reconstruire et démarrer les conteneurs
echo "🔨 Construction et démarrage des conteneurs..."
docker-compose up --build -d
echo ""

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier l'état des services
echo ""
echo "📊 État des services:"
docker-compose ps
echo ""

# Afficher les informations de connexion
echo "================================================"
echo "✅ Application démarrée avec succès!"
echo ""
echo "🔗 URLs d'accès (HTTPS):"
echo "   - Application: https://localhost"
echo "   - Backend API: https://localhost/api"
echo "   - Django Admin: https://localhost/admin"
echo "   - Keycloak: https://localhost/auth"
echo "   - Kibana (ELK): https://localhost:5601"
echo ""
echo "⚠️  IMPORTANT:"
echo "   Votre navigateur affichera un avertissement de sécurité car"
echo "   les certificats sont auto-signés. Vous devez accepter le risque."
echo ""
echo "📝 Pour voir les logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Pour arrêter l'application:"
echo "   docker-compose down"
echo "================================================"
