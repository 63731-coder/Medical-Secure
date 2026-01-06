#!/bin/bash

# Script de test pour vérifier la configuration TLS

echo "🔍 Test de la configuration TLS/HTTPS"
echo "====================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de test
test_check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# 1. Vérifier que les certificats existent
echo "1. Vérification des certificats..."
if [ -f "./certs/localhost.key" ] && [ -f "./certs/localhost.crt" ]; then
    echo -e "${GREEN}✓${NC} Certificats SSL trouvés"
    
    # Afficher les détails du certificat
    echo ""
    echo "Détails du certificat:"
    openssl x509 -in ./certs/localhost.crt -text -noout | grep -A 1 "Subject:"
    openssl x509 -in ./certs/localhost.crt -text -noout | grep -A 1 "Not After"
    echo ""
else
    echo -e "${RED}✗${NC} Certificats SSL manquants"
    echo "   Exécutez: cd certs && ./generate-certs.sh"
    exit 1
fi

# 2. Vérifier que Docker est en cours d'exécution
echo "2. Vérification de Docker..."
docker info > /dev/null 2>&1
test_check "Docker est actif"

# 3. Vérifier que les conteneurs sont en cours d'exécution
echo ""
echo "3. Vérification des conteneurs..."
for container in medical-nginx medical-backend medical-frontend medical-keycloak medical-postgres; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${GREEN}✓${NC} $container est actif"
    else
        echo -e "${YELLOW}⚠${NC} $container n'est pas actif"
    fi
done

# 4. Tester la connexion HTTPS
echo ""
echo "4. Test de connexion HTTPS..."

# Test nginx health check
if curl -k -s -f https://localhost/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Nginx répond (health check)"
else
    echo -e "${RED}✗${NC} Nginx ne répond pas"
fi

# 5. Tester les protocoles TLS
echo ""
echo "5. Test des protocoles TLS..."

# TLS 1.2
if openssl s_client -connect localhost:443 -tls1_2 < /dev/null 2>&1 | grep -q "Protocol.*TLSv1.2"; then
    echo -e "${GREEN}✓${NC} TLS 1.2 supporté"
else
    echo -e "${YELLOW}⚠${NC} TLS 1.2 non détecté"
fi

# TLS 1.3
if openssl s_client -connect localhost:443 -tls1_3 < /dev/null 2>&1 | grep -q "Protocol.*TLSv1.3"; then
    echo -e "${GREEN}✓${NC} TLS 1.3 supporté"
else
    echo -e "${YELLOW}⚠${NC} TLS 1.3 non détecté"
fi

# 6. Tester les headers de sécurité
echo ""
echo "6. Test des headers de sécurité..."

HEADERS=$(curl -k -s -I https://localhost/)

if echo "$HEADERS" | grep -q "Strict-Transport-Security"; then
    echo -e "${GREEN}✓${NC} HSTS header présent"
else
    echo -e "${YELLOW}⚠${NC} HSTS header manquant"
fi

if echo "$HEADERS" | grep -q "X-Frame-Options"; then
    echo -e "${GREEN}✓${NC} X-Frame-Options présent"
else
    echo -e "${YELLOW}⚠${NC} X-Frame-Options manquant"
fi

if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    echo -e "${GREEN}✓${NC} X-Content-Type-Options présent"
else
    echo -e "${YELLOW}⚠${NC} X-Content-Type-Options manquant"
fi

# 7. Tester la redirection HTTP -> HTTPS
echo ""
echo "7. Test de la redirection HTTP -> HTTPS..."
if curl -s -I http://localhost/ | grep -q "301\|Location.*https"; then
    echo -e "${GREEN}✓${NC} Redirection HTTP -> HTTPS active"
else
    echo -e "${YELLOW}⚠${NC} Redirection HTTP -> HTTPS non détectée"
fi

# 8. Résumé
echo ""
echo "====================================="
echo "📊 Résumé des tests"
echo "====================================="
echo ""
echo "URLs à tester dans le navigateur:"
echo "  • https://localhost"
echo "  • https://localhost/api"
echo "  • https://localhost/auth"
echo ""
echo "⚠️  N'oubliez pas d'accepter le certificat auto-signé dans votre navigateur!"
echo ""
