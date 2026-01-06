# Certificats SSL pour le développement

Ce dossier contient les certificats SSL auto-signés pour le développement en localhost.

## Génération des certificats

### Sur Linux/Mac:
```bash
chmod +x generate-certs.sh
./generate-certs.sh
```

### Sur Windows:
```cmd
generate-certs.bat
```

## Fichiers générés

- `localhost.key` - Clé privée (ne JAMAIS commiter)
- `localhost.crt` - Certificat auto-signé (ne JAMAIS commiter)

## ⚠️ Avertissement de sécurité

Ces certificats sont **auto-signés** et destinés **uniquement au développement local**.

- Votre navigateur affichera un avertissement de sécurité
- Vous devrez accepter manuellement le certificat
- **NE PAS utiliser en production**

## Accepter le certificat dans votre navigateur

### Chrome/Edge:
1. Cliquez sur "Avancé" ou "Advanced"
2. Cliquez sur "Continuer vers localhost (dangereux)" ou "Proceed to localhost (unsafe)"

### Firefox:
1. Cliquez sur "Avancé" ou "Advanced"
2. Cliquez sur "Accepter le risque et continuer" ou "Accept the Risk and Continue"

## Production

Pour la production, utilisez des certificats valides de:
- Let's Encrypt (gratuit)
- Une autorité de certification reconnue
