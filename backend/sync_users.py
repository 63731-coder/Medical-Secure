#!/usr/bin/env python
"""
Script de synchronisation automatique des utilisateurs depuis Keycloak vers Django
Usage: python sync_users.py
"""

import os
import sys
import django
import requests
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from med_secure.models import Patient, Doctor

def get_admin_token():
    """Obtient un token d'administration Keycloak"""
    token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
    try:
        response = requests.post(token_url, data={
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin123'
        }, timeout=10)
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'obtention du token admin: {e}")
        sys.exit(1)

def fetch_keycloak_user(keycloak_id, admin_token):
    """Récupère les données d'un utilisateur depuis Keycloak"""
    user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}"
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    try:
        response = requests.get(user_url, headers=headers, timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Erreur lors de la récupération de l'utilisateur {keycloak_id}: {e}")
        return None

def update_django_user(django_user, keycloak_data):
    """Met à jour les informations d'un utilisateur Django"""
    updated = False
    
    first_name = keycloak_data.get('firstName', '')
    last_name = keycloak_data.get('lastName', '')
    email = keycloak_data.get('email', '')
    username = keycloak_data.get('username', '')
    
    if django_user.first_name != first_name:
        django_user.first_name = first_name
        updated = True
    
    if django_user.last_name != last_name:
        django_user.last_name = last_name
        updated = True
    
    if django_user.email != email:
        django_user.email = email
        updated = True
    
    if django_user.username != username:
        django_user.username = username
        updated = True
    
    if updated:
        django_user.save()
    
    return updated

def sync_patients(admin_token):
    """Synchronise tous les patients"""
    patients = Patient.objects.select_related('user').all()
    updated_count = 0
    
    print(f"\n📋 Synchronisation de {patients.count()} patient(s)...")
    
    for patient in patients:
        keycloak_data = fetch_keycloak_user(patient.keycloak_id, admin_token)
        
        if keycloak_data is None:
            print(f"  ⚠️  Patient {patient.user.username} n'existe plus dans Keycloak")
            continue
        
        if update_django_user(patient.user, keycloak_data):
            name = f"{keycloak_data.get('firstName', '')} {keycloak_data.get('lastName', '')}".strip()
            print(f"  ✓ Patient mis à jour: {name or patient.user.username}")
            updated_count += 1
        else:
            print(f"  • Patient déjà à jour: {patient.user.username}")
    
    return updated_count

def get_user_roles(user_id, admin_token):
    """Récupère les rôles d'un utilisateur depuis Keycloak"""
    roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm"
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    try:
        response = requests.get(roles_url, headers=headers, timeout=10)
        if response.status_code == 200:
            roles = response.json()
            return [role['name'] for role in roles]
        return []
    except Exception as e:
        return []

def sync_doctors(admin_token):
    """Synchronise tous les docteurs depuis Keycloak vers Django"""
    # Récupérer tous les docteurs depuis Keycloak
    keycloak_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    try:
        response = requests.get(keycloak_url, headers=headers)
        if response.status_code != 200:
            print(f"  ⚠️  Erreur lors de la récupération des utilisateurs Keycloak")
            return 0
        
        all_users = response.json()
    except Exception as e:
        print(f"  ⚠️  Erreur: {e}")
        return 0
    
    # Filtrer les docteurs (ceux avec le rôle 'doctor')
    keycloak_doctors = []
    for user in all_users:
        user_roles = get_user_roles(user['id'], admin_token)
        if 'doctor' in user_roles:
            keycloak_doctors.append(user)
    
    print(f"\n🩺 Synchronisation de {len(keycloak_doctors)} docteur(s) depuis Keycloak...")
    
    updated_count = 0
    created_count = 0
    
    for kc_doctor in keycloak_doctors:
        keycloak_id = kc_doctor.get('id')
        username = kc_doctor.get('username')
        
        # Vérifier si le docteur existe déjà dans Django
        try:
            doctor = Doctor.objects.get(keycloak_id=keycloak_id)
            # Mettre à jour
            if update_django_user(doctor.user, kc_doctor):
                name = f"Dr. {kc_doctor.get('firstName', '')} {kc_doctor.get('lastName', '')}".strip()
                print(f"  ✓ Docteur mis à jour: {name or username}")
                updated_count += 1
            else:
                print(f"  • Docteur déjà à jour: {username}")
        except Doctor.DoesNotExist:
            # Créer le nouveau docteur
            try:
                from django.contrib.auth.models import User
                
                # Créer l'utilisateur Django
                django_user = User.objects.create_user(
                    username=username,
                    email=kc_doctor.get('email', ''),
                    first_name=kc_doctor.get('firstName', ''),
                    last_name=kc_doctor.get('lastName', '')
                )
                django_user.set_unusable_password()  # Géré par Keycloak
                django_user.save()
                
                # Créer le profil Doctor
                Doctor.objects.create(
                    user=django_user,
                    keycloak_id=keycloak_id,
                    organisation='Unknown'  # À définir manuellement
                )
                
                name = f"Dr. {kc_doctor.get('firstName', '')} {kc_doctor.get('lastName', '')}".strip()
                print(f"  ✨ Nouveau docteur créé: {name or username}")
                created_count += 1
            except Exception as e:
                print(f"  ⚠️  Erreur lors de la création de {username}: {e}")
    
    print(f"\n  📊 Total: {updated_count} mis à jour, {created_count} créés")
    return updated_count + created_count

def main():
    print("=" * 60)
    print("🔄 SYNCHRONISATION DES UTILISATEURS KEYCLOAK → DJANGO")
    print("=" * 60)
    
    # Vérification de la connexion Keycloak
    print("\n🔑 Connexion à Keycloak...")
    admin_token = get_admin_token()
    print("✓ Token admin obtenu")
    
    # Synchronisation
    patients_updated = sync_patients(admin_token)
    doctors_updated = sync_doctors(admin_token)
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ SYNCHRONISATION TERMINÉE")
    print(f"   • {patients_updated} patient(s) mis à jour")
    print(f"   • {doctors_updated} docteur(s) mis à jour")
    print("=" * 60)

if __name__ == '__main__':
    main()
