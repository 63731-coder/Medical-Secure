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

def sync_doctors(admin_token):
    """Synchronise tous les docteurs"""
    doctors = Doctor.objects.select_related('user').all()
    updated_count = 0
    
    print(f"\n🩺 Synchronisation de {doctors.count()} docteur(s)...")
    
    for doctor in doctors:
        keycloak_data = fetch_keycloak_user(doctor.keycloak_id, admin_token)
        
        if keycloak_data is None:
            print(f"  ⚠️  Docteur {doctor.user.username} n'existe plus dans Keycloak")
            continue
        
        if update_django_user(doctor.user, keycloak_data):
            name = f"Dr. {keycloak_data.get('firstName', '')} {keycloak_data.get('lastName', '')}".strip()
            print(f"  ✓ Docteur mis à jour: {name or doctor.user.username}")
            updated_count += 1
        else:
            print(f"  • Docteur déjà à jour: {doctor.user.username}")
    
    return updated_count

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
