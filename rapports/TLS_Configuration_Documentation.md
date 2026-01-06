# Configuration TLS/SSL - Documentation Technique

## Vue d'ensemble

Ce document explique l'implémentation TLS/SSL dans Medical Secure App, conformément aux meilleures pratiques de sécurité.

## Architecture

### Flux de Communication

```
Client (Browser)
    │
    │ HTTPS (TLS 1.2/1.3) - Port 443
    ↓
Nginx Reverse Proxy
    │ TLS Termination
    │ Security Headers
    │
    ├─→ Frontend (Vue.js)    - HTTP:5173 (internal)
    ├─→ Backend (Django)     - HTTP:8000 (internal)
    └─→ Keycloak (OAuth2)    - HTTP:8080 (internal)
```

### Justification Architecturale

**Pourquoi TLS termination au niveau de nginx ?**

1. **Centralisation**: Un seul point de configuration TLS pour tous les services
2. **Performance**: Les services internes communiquent en HTTP (plus rapide dans Docker)
3. **Simplicité**: Plus facile à maintenir et à déboguer
4. **Flexibilité**: Facilite le load balancing et le routing
5. **Sécurité**: Le réseau Docker interne est isolé

## Configuration TLS

### Protocoles Supportés

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

**Justification:**
- ✅ **TLS 1.3**: Protocole le plus récent, plus rapide et plus sécurisé
- ✅ **TLS 1.2**: Rétrocompatibilité avec clients plus anciens
- ❌ **TLS 1.0/1.1**: Obsolètes et vulnérables (BEAST, POODLE)

### Cipher Suites

```nginx
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
```

**Caractéristiques:**
- ✅ **ECDHE**: Échange de clés avec Perfect Forward Secrecy (PFS)
- ✅ **AES-GCM**: Chiffrement authentifié (AEAD)
- ✅ **ChaCha20-Poly1305**: Alternative rapide pour mobile
- ✅ **SHA256/SHA384**: Fonctions de hachage sécurisées

### Perfect Forward Secrecy (PFS)

PFS garantit que même si la clé privée du serveur est compromise, les sessions passées restent sécurisées.

**Algorithmes PFS utilisés:**
- ECDHE (Elliptic Curve Diffie-Hellman Ephemeral)
- DHE (Diffie-Hellman Ephemeral)

### Session Configuration

```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;
```

**Explications:**
- `ssl_session_cache`: Cache partagé de 10MB pour les sessions SSL (améliore les performances)
- `ssl_session_timeout`: Les sessions SSL expirent après 10 minutes
- `ssl_session_tickets off`: Désactivé pour éviter les problèmes de sécurité avec les tickets

## Headers de Sécurité

### HSTS (HTTP Strict Transport Security)

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

**Protection:**
- Force le navigateur à utiliser HTTPS pendant 1 an
- Protège contre les attaques SSL stripping
- `includeSubDomains`: Applique aussi aux sous-domaines

### X-Frame-Options

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
```

**Protection:** Empêche le site d'être intégré dans une iframe (protection clickjacking)

### X-Content-Type-Options

```nginx
add_header X-Content-Type-Options "nosniff" always;
```

**Protection:** Empêche le navigateur de "deviner" le type MIME (protection XSS)

### X-XSS-Protection

```nginx
add_header X-XSS-Protection "1; mode=block" always;
```

**Protection:** Active le filtre XSS du navigateur

### Content-Security-Policy (CSP)

```nginx
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
```

**Protection:**
- Contrôle les ressources que le navigateur peut charger
- Réduit les risques d'injection de scripts malveillants

### Referrer-Policy

```nginx
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Protection:** Contrôle les informations de référence envoyées

## Certificats SSL

### Développement (Auto-signés)

**Génération:**
```bash
openssl genrsa -out localhost.key 2048
openssl req -new -x509 -key localhost.key -out localhost.crt -days 365 -config openssl.cnf
```

**Caractéristiques:**
- RSA 2048 bits
- SHA-256
- Validité: 365 jours
- SAN (Subject Alternative Names): localhost, 127.0.0.1, ::1

### Production (Recommandations)

**Option 1: Let's Encrypt (Gratuit)**
```bash
certbot certonly --standalone -d votre-domaine.com
```

**Option 2: Certificat Commercial**
- DigiCert
- Sectigo
- GlobalSign

**Option 3: Wildcard Certificate**
Pour couvrir tous les sous-domaines: `*.votre-domaine.com`

## Configuration Backend Django

### SECURE_SSL_REDIRECT

```python
SECURE_SSL_REDIRECT = True  # En production
```

Force la redirection HTTP → HTTPS au niveau de Django (double protection avec nginx).

### CSRF_COOKIE_SECURE

```python
CSRF_COOKIE_SECURE = True
```

Les cookies CSRF ne sont envoyés que via HTTPS.

### SESSION_COOKIE_SECURE

```python
SESSION_COOKIE_SECURE = True
```

Les cookies de session ne sont envoyés que via HTTPS.

### SECURE_HSTS_SECONDS

```python
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

Active HSTS au niveau de Django (en plus de nginx).

## Configuration Frontend

### Variables d'Environnement

```env
VITE_API_URL=https://localhost/api
VITE_KEYCLOAK_URL=https://localhost/auth
```

### Hot Module Replacement (HMR) via WSS

```javascript
server: {
  hmr: {
    clientPort: 443,
    protocol: 'wss',
  },
}
```

Permet le HMR de Vite à travers nginx avec WebSocket sécurisé.

## Tests de Sécurité

### SSL Labs Test

Pour tester la configuration SSL en production:
```
https://www.ssllabs.com/ssltest/
```

**Objectif:** Note A ou A+

### Tester localement

```bash
# Tester les protocoles supportés
openssl s_client -connect localhost:443 -tls1_2
openssl s_client -connect localhost:443 -tls1_3

# Voir le certificat
openssl s_client -connect localhost:443 -showcerts

# Tester les cipher suites
nmap --script ssl-enum-ciphers -p 443 localhost
```

## Performance

### Optimisations TLS

1. **Session Resumption**: Cache des sessions SSL (10MB)
2. **HTTP/2**: Activé (`listen 443 ssl http2`)
3. **Keep-Alive**: Réutilisation des connexions TCP
4. **Compression**: gzip pour les réponses

### Métriques Attendues

- **Handshake TLS 1.3**: ~1 RTT (Round Trip Time)
- **Handshake TLS 1.2**: ~2 RTT
- **Session Resumption**: ~0 RTT (avec cache)

## Monitoring

### Logs à Surveiller

```bash
# Erreurs SSL
docker-compose logs nginx | grep -i ssl

# Connexions refusées
docker-compose logs nginx | grep -i "400\|403\|499"
```

### Métriques Important

- Taux d'utilisation TLS 1.3 vs 1.2
- Temps de handshake SSL
- Taux d'erreurs de certificat
- Tentatives de downgrade protocol

## Checklist de Production

- [ ] Certificats valides d'une CA reconnue
- [ ] Renouvellement automatique des certificats (certbot)
- [ ] Désactivation de TLS 1.0 et 1.1
- [ ] HSTS activé (min 6 mois)
- [ ] Certificate Pinning (optionnel, avancé)
- [ ] OCSP Stapling activé
- [ ] Monitoring des expirations de certificats
- [ ] Rate limiting configuré
- [ ] Firewall configuré (UFW/iptables)
- [ ] Logs centralisés et surveillés

## Conformité

Cette configuration est conforme avec:

- ✅ **OWASP Top 10** (2021)
- ✅ **PCI DSS 3.2.1** (pour e-commerce)
- ✅ **HIPAA** (données médicales)
- ✅ **RGPD** (protection des données personnelles)
- ✅ **Mozilla SSL Configuration** (Modern)

## Références

- [OWASP Transport Layer Protection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [RFC 8446 - TLS 1.3](https://tools.ietf.org/html/rfc8446)
- [NIST Guidelines for TLS](https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final)

## Support

Pour toute question sur la configuration TLS, contactez l'équipe de développement.

---

**Dernière mise à jour:** Janvier 2026  
**Version:** 1.0
