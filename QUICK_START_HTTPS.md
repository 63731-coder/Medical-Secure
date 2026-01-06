# 🚀 Guide de Démarrage Rapide - HTTPS/TLS

## Démarrage avec HTTPS (Recommandé)

### Windows
```cmd
start-https.bat
```

### Linux/Mac
```bash
chmod +x start-https.sh
./start-https.sh
```

## URLs d'Accès

- 🌐 **Application principale**: https://localhost
- 🔌 **API Backend**: https://localhost/api
- 👨‍💼 **Django Admin**: https://localhost/admin
- 🔐 **Keycloak**: https://localhost/auth
- 📊 **Kibana**: https://localhost:5601

## ⚠️ Avertissement de Sécurité

Votre navigateur affichera un avertissement car les certificats sont auto-signés pour le développement.

### Comment accepter le certificat:

**Chrome/Edge:**
1. Cliquez sur "Avancé" ou "Advanced"
2. Cliquez sur "Continuer vers localhost (dangereux)"

**Firefox:**
1. Cliquez sur "Avancé"
2. Cliquez sur "Accepter le risque et continuer"

## Architecture TLS

```
┌─────────────────┐
│  Browser        │
│  (HTTPS/TLS)    │
└────────┬────────┘
         │ Port 443 (HTTPS)
         ↓
┌────────────────────────┐
│  Nginx Reverse Proxy   │
│  - TLS Termination     │
│  - Security Headers    │
└────────┬───────────────┘
         │ HTTP (Docker Network)
         ↓
    ┌────┴────┐
    ↓         ↓
┌────────┐ ┌────────┐
│Frontend│ │Backend │
│Vue.js  │ │Django  │
└────────┘ └────────┘
```

## Sécurité TLS

✅ **TLS 1.2 & TLS 1.3**
✅ **Chiffrements forts** (ECDHE, AES-GCM, ChaCha20)
✅ **Perfect Forward Secrecy**
✅ **HSTS Headers** (Force HTTPS)
✅ **CSP Headers** (Content Security Policy)
✅ **HTTP → HTTPS Redirection**

## Commandes Utiles

### Voir les logs
```bash
docker-compose logs -f
```

### Logs d'un service spécifique
```bash
docker-compose logs -f nginx
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Arrêter l'application
```bash
docker-compose down
```

### Redémarrer avec rebuild
```bash
docker-compose up --build -d
```

### Vérifier l'état des services
```bash
docker-compose ps
```

## Régénérer les Certificats

Si nécessaire, régénérez les certificats SSL:

**Windows:**
```cmd
cd certs
generate-certs.bat
```

**Linux/Mac:**
```bash
cd certs
./generate-certs.sh
```

Puis redémarrez nginx:
```bash
docker-compose restart nginx
```

## Dépannage

### Le navigateur refuse la connexion
- Vérifiez que nginx est démarré: `docker ps | grep nginx`
- Vérifiez les logs nginx: `docker-compose logs nginx`

### Erreur de certificat
- Régénérez les certificats (voir ci-dessus)
- Assurez-vous que les fichiers `.crt` et `.key` existent dans `certs/`

### Les changements de code ne sont pas visibles
- Frontend: Le Hot Module Replacement (HMR) est actif via WebSocket sécurisé
- Backend: Redémarrez le conteneur: `docker-compose restart backend`

## Production

⚠️ **Pour la production:**
- Utilisez des certificats valides (Let's Encrypt, CA reconnue)
- Changez tous les mots de passe par défaut
- Désactivez DEBUG dans Django
- Configurez ALLOWED_HOSTS correctement
- Utilisez des secrets forts pour JWT/Session

---

📚 Pour plus d'informations, consultez le [README.md](README.md) principal.
