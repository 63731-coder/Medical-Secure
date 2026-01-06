#!/bin/bash

# Script pour générer des certificats SSL auto-signés pour localhost
# Pour le développement uniquement

CERTS_DIR="$(dirname "$0")"
DAYS_VALID=365

echo "🔐 Génération des certificats SSL auto-signés pour localhost..."

# Vérifier si OpenSSL est installé
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Supprimer les anciens certificats s'ils existent
rm -f "$CERTS_DIR/localhost.key" "$CERTS_DIR/localhost.crt" "$CERTS_DIR/localhost.csr"

# Générer la clé privée
echo "📝 Génération de la clé privée..."
openssl genrsa -out "$CERTS_DIR/localhost.key" 2048

# Créer un fichier de configuration pour le certificat
cat > "$CERTS_DIR/openssl.cnf" <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = BE
ST = Belgium
L = Brussels
O = Medical Secure
OU = Development
CN = localhost

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Générer le certificat auto-signé
echo "📜 Génération du certificat auto-signé..."
openssl req -new -x509 -key "$CERTS_DIR/localhost.key" \
    -out "$CERTS_DIR/localhost.crt" \
    -days $DAYS_VALID \
    -config "$CERTS_DIR/openssl.cnf"

# Nettoyer le fichier de configuration temporaire
rm -f "$CERTS_DIR/openssl.cnf"

# Vérifier que les fichiers ont été créés
if [ -f "$CERTS_DIR/localhost.key" ] && [ -f "$CERTS_DIR/localhost.crt" ]; then
    echo "✅ Certificats générés avec succès!"
    echo ""
    echo "📁 Fichiers créés:"
    echo "   - $CERTS_DIR/localhost.key (Clé privée)"
    echo "   - $CERTS_DIR/localhost.crt (Certificat)"
    echo ""
    echo "⚠️  IMPORTANT: Ces certificats sont auto-signés et destinés au développement uniquement."
    echo "    Votre navigateur affichera un avertissement de sécurité. Vous devrez accepter le risque."
    echo ""
    echo "🔍 Pour voir les détails du certificat:"
    echo "    openssl x509 -in $CERTS_DIR/localhost.crt -text -noout"
else
    echo "❌ Erreur lors de la génération des certificats"
    exit 1
fi
