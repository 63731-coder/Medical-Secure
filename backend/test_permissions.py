#!/usr/bin/env python
"""
Script de test pour le système de permissions patient-médecin
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_workflow():
    """Test du workflow complet"""
    
    # 1. Créer un compte patient
    print("\n=== 1. Création d'un compte PATIENT ===")
    patient_data = {
        "username": "test_patient",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "email": "patient@test.com",
        "user_type": "patient",
        "date_of_birth": "1990-01-15"
    }
    
    resp = requests.post(f"{BASE_URL}/register/", json=patient_data)
    if resp.status_code == 201:
        print("✓ Patient créé avec succès")
        patient_token = resp.json()['token']
        patient_id = resp.json()['user']['profile']['id']
    else:
        print(f"✗ Erreur: {resp.json()}")
        return
    
    # 2. Créer un compte médecin
    print("\n=== 2. Création d'un compte MÉDECIN ===")
    doctor_data = {
        "username": "test_doctor",
        "password": "SecurePass123!",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "doctor@test.com",
        "user_type": "doctor",
        "organisation": "City Hospital"
    }
    
    resp = requests.post(f"{BASE_URL}/register/", json=doctor_data)
    if resp.status_code == 201:
        print("✓ Médecin créé avec succès")
        doctor_token = resp.json()['token']
        doctor_id = resp.json()['user']['profile']['id']
    else:
        print(f"✗ Erreur: {resp.json()}")
        return
    
    # 3. Médecin envoie une requête au patient
    print("\n=== 3. Médecin envoie une requête d'accès ===")
    resp = requests.post(
        f"{BASE_URL}/requests/",
        json={"patient_id": patient_id},
        headers={"Authorization": f"Token {doctor_token}"}
    )
    if resp.status_code == 201:
        print("✓ Requête envoyée avec succès")
        request_id = resp.json()['id']
    else:
        print(f"✗ Erreur: {resp.json()}")
        return
    
    # 4. Patient voit les requêtes
    print("\n=== 4. Patient consulte ses requêtes ===")
    resp = requests.get(
        f"{BASE_URL}/requests/",
        headers={"Authorization": f"Token {patient_token}"}
    )
    if resp.status_code == 200:
        requests_list = resp.json()
        pending = [r for r in requests_list if r['status'] == 'pending']
        print(f"✓ {len(pending)} requête(s) en attente")
        if pending:
            print(f"  - De: Dr. {pending[0]['doctor']['user']['last_name']}")
    else:
        print(f"✗ Erreur: {resp.json()}")
    
    # 5. Patient approuve la requête
    print("\n=== 5. Patient approuve la requête ===")
    resp = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve/",
        headers={"Authorization": f"Token {patient_token}"}
    )
    if resp.status_code == 200:
        print("✓ Requête approuvée")
    else:
        print(f"✗ Erreur: {resp.json()}")
        return
    
    # 6. Médecin voit le patient dans sa liste
    print("\n=== 6. Médecin consulte sa liste de patients ===")
    resp = requests.get(
        f"{BASE_URL}/patients/",
        headers={"Authorization": f"Token {doctor_token}"}
    )
    if resp.status_code == 200:
        patients = resp.json()
        print(f"✓ {len(patients)} patient(s) dans la liste")
        if patients:
            print(f"  - {patients[0]['user']['first_name']} {patients[0]['user']['last_name']}")
    else:
        print(f"✗ Erreur: {resp.json()}")
    
    # 7. Patient voit le médecin dans sa liste
    print("\n=== 7. Patient consulte sa liste de médecins ===")
    resp = requests.get(
        f"{BASE_URL}/profile/",
        headers={"Authorization": f"Token {patient_token}"}
    )
    if resp.status_code == 200:
        profile = resp.json()
        doctors = profile['profile']['appointed_doctors']
        print(f"✓ {len(doctors)} médecin(s) dans la liste")
        if doctors:
            print(f"  - Dr. {doctors[0]['user']['last_name']} ({doctors[0]['organisation']})")
    else:
        print(f"✗ Erreur: {resp.json()}")
    
    print("\n=== Test terminé avec succès! ===\n")


if __name__ == "__main__":
    try:
        test_workflow()
    except requests.exceptions.ConnectionError:
        print("\n✗ Erreur: Impossible de se connecter au serveur")
        print("Assurez-vous que le serveur Django est démarré sur http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {str(e)}")
