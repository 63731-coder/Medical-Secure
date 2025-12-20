# Rapport de Sécurité - Checklist 1: Confidentialité

## ✅ 1. Est-ce que les données sensibles sont transmises et stockées correctement ?

### 🔐 **OUI - Implémentation du chiffrement côté client (Zero Trust)**

#### **A. Chiffrement des fichiers médicaux côté client**

**Fichier:** `frontend/src/utils/crypto.js`

**Lignes 32-40 - Fonction de chiffrement:**
```javascript
export const encryptData = (data) => {
    if (!SECRET_KEY) {
        console.error("Aucune clé de chiffrement définie !");
        return null;
    }
    return CryptoJS.AES.encrypt(data, SECRET_KEY).toString();
};
```
📸 **Screenshot:** Lignes 32-40 de `crypto.js`

**Explication ligne par ligne:**
- **Ligne 32**: Fonction exportée qui prend les données sensibles à chiffrer
- **Ligne 33**: Vérification que la clé de chiffrement existe (sécurité)
- **Ligne 34**: Message d'erreur si pas de clé (l'utilisateur doit être connecté)
- **Ligne 35**: Retourne `null` si impossible de chiffrer (évite d'envoyer en clair)
- **Ligne 37**: Chiffrement **AES-256** avec la clé secrète de l'utilisateur
- **Ligne 37**: `.toString()` convertit le résultat en format Base64 pour transmission
- **Résultat**: Données illisibles sans la clé, stockables et transmissibles en toute sécurité

---

**Lignes 43-51 - Fonction de déchiffrement:**
```javascript
export const decryptData = (cipherText) => {
    if (!SECRET_KEY) return null;
    try {
        const bytes = CryptoJS.AES.decrypt(cipherText, SECRET_KEY);
        return bytes.toString(CryptoJS.enc.Utf8);
    } catch (e) {
        console.error("Erreur de déchiffrement", e);
        return "Donnée illisible";
    }
};
```
📸 **Screenshot:** Lignes 43-51 de `crypto.js`

**Explication ligne par ligne:**
- **Ligne 43**: Fonction qui déchiffre les données chiffrées reçues du serveur
- **Ligne 44**: Retourne `null` si pas de clé (impossible de déchiffrer)
- **Ligne 45**: Bloc `try` pour gérer les erreurs de déchiffrement
- **Ligne 46**: Déchiffrement AES avec la clé secrète de l'utilisateur
- **Ligne 47**: Conversion des bytes déchiffrés en texte UTF-8 lisible
- **Ligne 48-50**: Si erreur (mauvaise clé, données corrompues), retourne message d'erreur
- **Résultat**: Seul l'utilisateur avec la bonne clé peut lire les données

---

#### **B. Génération de clé depuis le mot de passe utilisateur**

**Fichier:** `frontend/src/utils/crypto.js`

**Lignes 14-25 - Dérivation de clé avec PBKDF2:**
```javascript
export const deriveKeyFromPassword = (password, salt = 'mon_sel_fixe_pour_le_projet') => {
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 1000
    });
    SECRET_KEY = key.toString();
    sessionStorage.setItem('encryptionKey', SECRET_KEY);
    console.log("Clé de chiffrement générée (en mémoire uniquement).");
};
```
📸 **Screenshot:** Lignes 14-25 de `crypto.js`

**Explication ligne par ligne:**
- **Ligne 14**: Fonction appelée au login, prend le mot de passe + sel (salt)
- **Ligne 15**: **PBKDF2** = algorithme qui transforme un mot de passe en clé cryptographique robuste
- **Ligne 16**: `keySize: 256/32` = génère une clé de 256 bits (très sécurisé)
- **Ligne 17**: `iterations: 1000` = applique l'algorithme 1000 fois (ralentit les attaques par force brute)
- **Ligne 19**: Stocke la clé générée dans la variable globale `SECRET_KEY`
- **Ligne 20**: Sauvegarde dans `sessionStorage` (mémoire temporaire du navigateur)
- **Ligne 20**: `sessionStorage` est vidé à la fermeture du navigateur = sécurité maximale
- **Important**: Le serveur ne reçoit JAMAIS cette clé, elle reste côté client uniquement

---

#### **C. Utilisation du chiffrement lors de l'upload**

**Fichier:** `frontend/src/views/UploadView.vue`

**Lignes 68-72 - Chiffrement avant envoi:**
```javascript
const base64Content = await readFileAsBase64(file);
const encryptedContent = encryptData(base64Content);

if (!encryptedContent) {
    throw new Error('Échec du chiffrement');
}
```
📸 **Screenshot:** Lignes 68-72 de `UploadView.vue`

**Explication ligne par ligne:**
- **Ligne 68**: Lecture du fichier et conversion en Base64 (format texte transmissible)
- **Ligne 69**: Appel de `encryptData()` pour chiffrer le contenu Base64 en AES-256
- **Ligne 71**: Vérification que le chiffrement a réussi
- **Ligne 72**: Si échec, bloque l'upload (JAMAIS d'envoi en clair)
- **Résultat**: Le serveur reçoit uniquement des données déjà chiffrées côté client

---

#### **D. Stockage chiffré sur le serveur**

**Fichier:** `backend/media/medical_records/`

**Preuve visible dans le système de fichiers:**
```
QCM_RGPD_Complet_0OqjyXG.pdf.enc
QCM_RGPD_Complet_2icwCHg.pdf.enc
QCM_RGPD_Complet_HkpGkfN.pdf.enc
test_3.enc
```
📸 **Screenshot:** Contenu du dossier `backend/media/medical_records/`

**Explication:**
- Tous les fichiers ont l'extension `.enc` (encrypted)
- Le serveur stocke uniquement des données chiffrées
- Un administrateur ne peut **pas** lire ces fichiers sans la clé

---

## ✅ 2. Est-ce que les requêtes sensibles sont transmises de manière sécurisée ?

### 🔐 **OUI - Authentification par Token + Configuration HTTPS**

#### **A. Authentification Token pour toutes les requêtes**

**Fichier:** `frontend/src/services/api.js`

**Lignes 11-17 - Intercepteur d'authentification:**
```javascript
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    return config;
});
```
📸 **Screenshot:** Lignes 11-17 de `api.js`

**Explication ligne par ligne:**
- **Ligne 11**: Intercepteur Axios = fonction exécutée automatiquement avant chaque requête
- **Ligne 12**: Récupère le token d'authentification depuis le stockage local du navigateur
- **Ligne 13**: Vérifie que le token existe (utilisateur connecté)
- **Ligne 14**: Ajoute le header `Authorization: Token xyz123` à la requête
- **Ligne 16**: Retourne la configuration modifiée pour envoyer la requête
- **Résultat**: Toutes les requêtes API incluent automatiquement l'authentification

---

#### **B. Protection par permissions côté serveur**

**Fichier:** `backend/config/settings.py`

**Lignes 119-126 - Configuration DRF:**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```
📸 **Screenshot:** Lignes 119-126 de `settings.py`

**Explication ligne par ligne:**
- **Ligne 119**: Configuration globale de Django REST Framework (DRF)
- **Ligne 120**: Liste des méthodes d'authentification acceptées
- **Ligne 121**: `TokenAuthentication` = vérifie le token dans le header `Authorization`
- **Ligne 122**: `SessionAuthentication` = pour l'interface admin Django
- **Ligne 124**: Permissions par défaut appliquées à TOUTES les routes API
- **Ligne 125**: `IsAuthenticated` = bloque toute requête sans token valide
- **Résultat**: Aucune donnée sensible accessible sans authentification

---

#### **C. Configuration HTTPS et Headers de sécurité**

**Fichier:** `backend/config/settings.py`

**Lignes 165-188 - Paramètres de sécurité HTTPS:**
```python
# HTTPS/SSL (False for local dev, True for production)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS - Force HTTPS for 1 year after first visit
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
SECURE_BROWSER_XSS_FILTER = True     # XSS protection
X_FRAME_OPTIONS = 'DENY'             # Prevent clickjacking

# Secure Cookies (HttpOnly prevents XSS, SameSite prevents CSRF)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
```
📸 **Screenshot:** Lignes 165-188 de `settings.py`

**Explication ligne par ligne:**
- **Ligne 166**: `SECURE_SSL_REDIRECT` = Force redirection HTTP → HTTPS (False en dev, True en prod)
- **Ligne 167-168**: Cookies sécurisés = envoyés uniquement sur HTTPS en production
- **Ligne 169**: Détecte si derrière un proxy HTTPS (ex: nginx, Apache)
- **Ligne 172**: `HSTS` = Force HTTPS pendant 31 536 000 secondes (1 an)
- **Ligne 173**: HSTS s'applique aussi aux sous-domaines (*.exemple.com)
- **Ligne 174**: Précharge HSTS dans les navigateurs = HTTPS obligatoire dès la 1ère visite
- **Ligne 177**: Empêche le navigateur de deviner le type MIME (sécurité)
- **Ligne 178**: Active le filtre XSS du navigateur (protection injection de code)
- **Ligne 179**: `X_FRAME_OPTIONS='DENY'` = Interdit l'affichage en iframe (anti-clickjacking)
- **Ligne 182-183**: `HttpOnly` = JavaScript ne peut pas lire les cookies (protection XSS)
- **Ligne 184-185**: `SameSite='Lax'` = Cookies non envoyés sur requêtes cross-site (protection CSRF)
- **Résultat**: Transmission sécurisée HTTPS + protection contre XSS, CSRF, clickjacking

# Cookie security settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
```
📸 **Screenshot:** Lignes 165-196 de `settings.py`

**Explication:**
- **HSTS** (HTTP Strict Transport Security) : Force HTTPS pendant 1 an
- **SECURE_CONTENT_TYPE_NOSNIFF** : Empêche l'interprétation erronée des types MIME
- **X_FRAME_OPTIONS='DENY'** : Protection contre le clickjacking
- **HttpOnly cookies** : Les cookies ne sont pas accessibles via JavaScript (protection XSS)
- **SameSite cookies** : Protection CSRF

---

#### **D. Validation de password côté serveur**

**Fichier:** `backend/config/settings.py`

**Lignes 105-116 - Validateurs de mot de passe:**
```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```
📸 **Screenshot:** Lignes 105-116 de `settings.py`

**Explication ligne par ligne:**
- **Ligne 105**: Liste des validateurs Django pour renforcer les mots de passe
- **Ligne 107**: `UserAttributeSimilarityValidator` = Empêche mot de passe similaire au username/email
- **Ligne 110**: `MinimumLengthValidator` = Impose longueur minimum (8 caractères par défaut)
- **Ligne 113**: `CommonPasswordValidator` = Refuse les mots de passe courants (password123, etc.)
- **Ligne 116**: `NumericPasswordValidator` = Refuse les mots de passe purement numériques
- **Important**: Django hash automatiquement avec PBKDF2-SHA256 (30 000 itérations)
- **Résultat**: Mots de passe robustes + stockage sécurisé (hashé, jamais en clair)

---

## ⚠️ 3. Est-ce qu'un administrateur système peut accéder aux données sensibles ?

### 🔐 **NON - Architecture Zero Trust**

#### **A. Fichiers chiffrés côté client uniquement**

**Fichier:** `backend/med_secure/views.py`

**Lignes 650-653 - Téléchargement de fichiers chiffrés:**
```python
# Return file (already encrypted)
response = FileResponse(medical_file.file.open('rb'))
response['Content-Disposition'] = f'attachment; filename="{medical_file.file.name}"'
return response
```
📸 **Screenshot:** Lignes 650-653 de `views.py`

**Explication ligne par ligne:**
- **Ligne 650**: Commentaire confirmant que le fichier est déjà chiffré côté client
- **Ligne 651**: `FileResponse` = renvoie le fichier binaire (`'rb'`) tel quel
- **Ligne 652**: Header HTTP qui définit le nom du fichier au téléchargement
- **Ligne 653**: Retourne la réponse HTTP avec le fichier
- **Important**: Le serveur ne déchiffre jamais, il retourne le blob chiffré
- **Résultat**: Même un administrateur système avec accès root voit uniquement des données chiffrées AES-256

---

#### **B. Contrôle d'accès strict**

**Fichier:** `backend/med_secure/views.py`

**Lignes 638-648 - Vérification des permissions:**
```python
# Security check: user has access to this file
if hasattr(request.user, 'patient_profile'):
    if medical_file.patient != request.user.patient_profile:
        return Response({'error': 'Permission denied'}, 
                      status=status.HTTP_403_FORBIDDEN)
elif hasattr(request.user, 'doctor_profile'):
    if not medical_file.patient.appointed_doctors.filter(
        id=request.user.doctor_profile.id
    ).exists():
        return Response({'error': 'Permission denied'}, 
                      status=status.HTTP_403_FORBIDDEN)
```
📸 **Screenshot:** Lignes 638-648 de `views.py`

**Explication ligne par ligne:**
- **Ligne 638**: Commentaire indiquant la vérification de sécurité
- **Ligne 639**: Vérifie si l'utilisateur est un patient
- **Ligne 640**: Compare si le fichier médical appartient bien à CE patient
- **Ligne 641-642**: Refuse l'accès (HTTP 403) si le patient tente d'accéder au fichier d'un autre
- **Ligne 643**: Sinon, vérifie si l'utilisateur est un docteur
- **Ligne 644-646**: Vérifie que le docteur est bien appointé par ce patient
- **Ligne 647**: `.exists()` = requête optimisée pour vérifier la relation docteur-patient
- **Ligne 649-650**: Refuse l'accès si le docteur n'est pas autorisé par le patient
- **Résultat**: Principe du **least privilege** - accès uniquement aux données strictement nécessaires

---

#### **C. Système d'approbation patient**

**Fichier:** `backend/med_secure/models.py`

**Lignes 88-110 - Modèle FileActionRequest:**
```python
class FileActionRequest(models.Model):
    """
    Request for a file action (upload, edit, delete) initiated by a doctor.
    Requires approval from the patient.
    """
    ACTION_CHOICES = [
        ('upload', 'Upload'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    patient = models.ForeignKey(Patient, ...)
    doctor = models.ForeignKey(Doctor, ...)
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
```
📸 **Screenshot:** Lignes 88-110 de `models.py`

**Explication ligne par ligne:**
- **Ligne 88**: Modèle de base de données pour gérer les demandes d'action des docteurs
- **Ligne 90-91**: Documentation : les docteurs doivent demander l'approbation du patient
- **Ligne 93-97**: `ACTION_CHOICES` = types d'actions possibles (upload, edit, delete)
- **Ligne 99-103**: `STATUS_CHOICES` = états de la demande (en attente, approuvé, rejeté)
- **Ligne 105**: Référence au patient concerné par la demande
- **Ligne 106**: Référence au docteur qui fait la demande
- **Ligne 107**: Type d'action demandée (upload/edit/delete)
- **Ligne 108**: Statut par défaut = `'pending'` (en attente d'approbation)
- **Principe**: Le **patient garde le contrôle total** - rien ne se passe sans son autorisation
- **Résultat**: Même les docteurs autorisés ne peuvent pas modifier les données sans approbation explicite
- Principe de **least privilege** : même les docteurs n'ont pas accès sans autorisation

---

## 📊 Résumé de la conformité

| Question | Conforme | Implémentation |
|----------|----------|----------------|
| **Données transmises et stockées correctement ?** | ✅ OUI | Chiffrement AES-256 côté client, HTTPS, stockage chiffré (.enc) |
| **Requêtes sensibles transmises de manière sécurisée ?** | ✅ OUI | Token Authentication, HTTPS configuré, Headers de sécurité (HSTS, XSS, CSRF) |
| **Administrateur peut accéder aux données sensibles ?** | ✅ NON | Architecture Zero Trust : clé de déchiffrement uniquement côté client, fichiers illisibles sans la clé |

---

## 🛡️ Points forts de sécurité

1. **Zero Trust Architecture** : Le serveur ne peut jamais lire les données médicales
2. **Chiffrement end-to-end** : Données chiffrées du client au stockage
3. **PBKDF2 Key Derivation** : Clé robuste dérivée du mot de passe
4. **Contrôle d'accès granulaire** : Patients et docteurs ont des permissions strictes
5. **Système d'approbation** : Les patients contrôlent l'accès à leurs données
6. **Headers de sécurité** : HSTS, XSS protection, Clickjacking protection
7. **Cookies sécurisés** : HttpOnly, Secure (en production), SameSite

---

## ⚠️ Recommandations pour la production

### À activer en production :
1. Dans `settings.py`, modifier :
   - `SECURE_SSL_REDIRECT = True`
   - `SESSION_COOKIE_SECURE = True`
   - `CSRF_COOKIE_SECURE = True`
   - `DEBUG = False`

2. Utiliser un reverse proxy (nginx) avec certificat SSL/TLS

3. Améliorer le salt PBKDF2 :
   - Utiliser un salt unique par utilisateur (stocké en clair)
   - Augmenter le nombre d'itérations PBKDF2 à 100 000+

4. Implémenter la rotation des tokens d'authentification

---

## 📸 Liste des screenshots à prendre

1. **Ligne 32-40** : `frontend/src/utils/crypto.js` - Fonction `encryptData`
2. **Ligne 43-51** : `frontend/src/utils/crypto.js` - Fonction `decryptData`
3. **Ligne 14-25** : `frontend/src/utils/crypto.js` - Dérivation PBKDF2
4. **Ligne 68-72** : `frontend/src/views/UploadView.vue` - Chiffrement upload
5. **Dossier** : `backend/media/medical_records/` - Fichiers `.enc`
6. **Ligne 11-17** : `frontend/src/services/api.js` - Intercepteur token
7. **Ligne 119-126** : `backend/config/settings.py` - Config DRF
8. **Ligne 165-196** : `backend/config/settings.py` - Sécurité HTTPS
9. **Ligne 105-116** : `backend/config/settings.py` - Validateurs password
10. **Ligne 650-653** : `backend/med_secure/views.py` - Download chiffré
11. **Ligne 638-648** : `backend/med_secure/views.py` - Vérification permissions
12. **Ligne 88-110** : `backend/med_secure/models.py` - FileActionRequest

---

**Date du rapport:** 20 décembre 2025  
**Projet:** Medical Secure Platform  
**Auteur:** 60991 - 63731 -  -  -  
