# Guide du Système de Gestion des Dossiers Médicaux Sécurisé

## ✅ Fonctionnalités Implémentées

### 1. **Modèles de Données**
- **Doctor**: Profil médecin avec organisation
- **Patient**: Profil patient avec date de naissance et médecins assignés
- **MedicalFile**: Fichiers médicaux avec traçabilité de l'uploadeur
- **FileActionRequest**: Demandes d'actions sur fichiers (upload/modify/delete)
- **AppointmentRequest**: Demandes d'assignation médecin-patient
- **Notification**: Système de notifications pour toutes les actions
- **AuditLog**: Journalisation complète pour audit de sécurité

### 2. **Système de Permissions**
#### Patient peut:
- ✅ Voir son propre dossier médical
- ✅ Ajouter/modifier/supprimer ses fichiers directement
- ✅ Approuver/refuser les demandes des médecins
- ✅ Recevoir des notifications pour toute demande
- ✅ Ajouter/retirer des médecins de sa liste
- ✅ Consulter l'historique d'audit de son dossier

#### Médecin assigné peut:
- ✅ Voir les dossiers des patients assignés (fichiers approuvés uniquement)
- ✅ Demander à ajouter/modifier/supprimer des fichiers
- ✅ Recevoir des notifications sur l'état de ses demandes
- ✅ Demander à être assigné à un patient
- ✅ Consulter ses propres logs d'audit

#### Sécurité:
- ✅ Contrôle d'accès strict avant toute action
- ✅ Journalisation complète (AuditLog)
- ✅ Notifications en temps différé (API REST)
- ✅ Traçabilité de toutes les actions

### 3. **API Endpoints**

#### Authentification
- `POST /api/register/` - Inscription (patient ou médecin)
- `POST /api/login/` - Connexion
- `POST /api/logout/` - Déconnexion
- `GET /api/profile/` - Profil utilisateur

#### Gestion des Médecins
- `GET /api/doctors/` - Liste des médecins
- `GET /api/doctors/{id}/` - Détails d'un médecin
- `POST /api/appointments/request/` - Demande d'assignation

#### Gestion des Patients
- `GET /api/patients/` - Liste des patients (filtrée selon rôle)
- `POST /api/patients/{id}/add-doctor/` - Ajouter un médecin
- `DELETE /api/patients/{id}/remove-doctor/{doctor_id}/` - Retirer un médecin
- `GET /api/patients/{id}/appointment-requests/` - Demandes en attente
- `POST /api/patients/{id}/appointment-requests/{req_id}/respond/` - Répondre à une demande

#### Gestion des Fichiers Médicaux
- `GET /api/files/` - Liste des fichiers
- `POST /api/files/` - Upload de fichier (direct ou demande)
- `GET /api/files/{id}/` - Détails d'un fichier
- `PUT/PATCH /api/files/{id}/` - Modifier un fichier
- `DELETE /api/files/{id}/` - Supprimer un fichier
- `GET /api/files/{id}/download/` - Télécharger un fichier
- `GET /api/files/pending-file-actions/` - Actions en attente
- `POST /api/files/respond-file-action/` - Répondre à une action

#### Notifications
- `GET /api/notifications/` - Liste des notifications
- `GET /api/notifications/{id}/` - Détails d'une notification
- `POST /api/notifications/{id}/mark-read/` - Marquer comme lue
- `POST /api/notifications/mark-all-read/` - Tout marquer comme lu
- `GET /api/notifications/unread-count/` - Nombre de non-lues

#### Audit & Sécurité
- `GET /api/audit-logs/` - Historique d'audit
- `GET /api/audit-logs/{id}/` - Détails d'un log
- `GET /api/audit-logs/security-events/` - Événements de sécurité

## 📝 Tests Recommandés

### Scénario 1: Inscription et Configuration
```bash
# 1. Créer un patient
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "patient1",
    "password": "SecurePass123!",
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "patient@test.com",
    "user_type": "patient",
    "date_of_birth": "1990-01-15"
  }'

# 2. Créer un médecin
curl -X POST http://127.0.0.1:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor1",
    "password": "SecurePass456!",
    "first_name": "Marie",
    "last_name": "Martin",
    "email": "doctor@hospital.com",
    "user_type": "doctor",
    "organisation": "Hôpital Central"
  }'
```

### Scénario 2: Demande d'Assignation Médecin
```bash
# 1. Médecin se connecte
curl -X POST http://127.0.0.1:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "doctor1", "password": "SecurePass456!"}'

# 2. Médecin demande assignation (utiliser token reçu)
curl -X POST http://127.0.0.1:8000/api/appointments/request/ \
  -H "Authorization: Token {doctor_token}" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1}'

# 3. Patient vérifie ses notifications
curl -X GET http://127.0.0.1:8000/api/notifications/ \
  -H "Authorization: Token {patient_token}"

# 4. Patient approuve la demande
curl -X POST http://127.0.0.1:8000/api/patients/1/appointment-requests/1/respond/ \
  -H "Authorization: Token {patient_token}" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}'
```

### Scénario 3: Gestion des Fichiers avec Approbation
```bash
# 1. Patient upload un fichier directement
curl -X POST http://127.0.0.1:8000/api/files/ \
  -H "Authorization: Token {patient_token}" \
  -F "file=@test_file.pdf" \
  -F "name=Analyse de sang" \
  -F "description=Résultats du 15/12/2024"

# 2. Médecin demande à ajouter un fichier
curl -X POST http://127.0.0.1:8000/api/files/ \
  -H "Authorization: Token {doctor_token}" \
  -F "file=@prescription.pdf" \
  -F "name=Prescription" \
  -F "description=Traitement antibiotique" \
  -F "patient_id=1"

# 3. Patient vérifie les demandes en attente
curl -X GET http://127.0.0.1:8000/api/files/pending-file-actions/ \
  -H "Authorization: Token {patient_token}"

# 4. Patient approuve l'upload
curl -X POST http://127.0.0.1:8000/api/files/respond-file-action/ \
  -H "Authorization: Token {patient_token}" \
  -H "Content-Type: application/json" \
  -d '{"request_id": 1, "action": "approve"}'
```

## 🔒 Prochaines Étapes de Sécurité

### Priorité HAUTE
1. **Chiffrement E2E côté client** - Chiffrer toutes les données sensibles avant envoi
2. **JWT avec refresh tokens** - Remplacer Token par JWT pour plus de sécurité
3. **Chiffrement des fichiers** - Chiffrer les fichiers avant stockage serveur
4. **HTTPS/TLS** - Sécuriser toutes les communications
5. **Bcrypt/Scrypt** - Améliorer le hachage des mots de passe

### Priorité MOYENNE
6. **Rate limiting** - Prévenir les attaques par déni de service
7. **2FA** - Authentification à deux facteurs
8. **Signature numérique** - Signer les fichiers médicaux
9. **WebSockets** - Notifications en temps réel

### Pour Master
10. **PKI et certificats** - Infrastructure à clés publiques pour médecins
11. **Métadonnées avancées** - Détection d'anomalies
12. **Logs immutables** - Hash chains pour l'audit

## 🧪 Vérification de Sécurité

### Tests de Permissions
- ✅ Un patient ne peut voir que ses propres fichiers
- ✅ Un médecin ne voit que les fichiers approuvés de ses patients assignés
- ✅ Les actions des médecins nécessitent l'approbation du patient
- ✅ Toutes les actions sont journalisées dans AuditLog
- ✅ Les notifications sont envoyées aux bonnes personnes

### Points d'Attention
- ⚠️ Les fichiers sont stockés en clair (à chiffrer)
- ⚠️ Authentification Token simple (à remplacer par JWT)
- ⚠️ Pas de HTTPS configuré (à ajouter)
- ⚠️ Mots de passe avec hashage Django standard (améliorer avec bcrypt)

## 📌 Notes Importantes

1. **Serveur non fiable**: Le système est conçu pour ne jamais faire confiance au serveur
2. **Patient au centre**: Le patient contrôle toutes les actions sur ses données
3. **Traçabilité complète**: Chaque action est enregistrée dans AuditLog
4. **Notifications**: Système complet de notifications pour toutes les interactions
5. **Permissions strictes**: Vérifications multiples avant chaque action

---

**Statut**: Système de base fonctionnel ✅
**Sécurité**: À renforcer avec chiffrement E2E et JWT 🔧
**Deadline**: 6 janvier 2025
