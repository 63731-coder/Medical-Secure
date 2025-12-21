from django.core.management.base import BaseCommand
from django.conf import settings
from med_secure.models import Doctor, Patient
import requests


class Command(BaseCommand):
    help = 'Synchronize user information from Keycloak to Django'

    def handle(self, *args, **options):
        # Get admin token
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        token_data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin123'
        }
        
        try:
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            admin_token = token_response.json()['access_token']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get admin token: {e}'))
            return

        headers = {'Authorization': f'Bearer {admin_token}'}

        # Sync all doctors
        for doctor in Doctor.objects.all():
            try:
                user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{doctor.keycloak_id}"
                response = requests.get(user_url, headers=headers)
                response.raise_for_status()
                keycloak_user = response.json()
                
                # Update Django user
                doctor.user.first_name = keycloak_user.get('firstName', '')
                doctor.user.last_name = keycloak_user.get('lastName', '')
                doctor.user.email = keycloak_user.get('email', '')
                doctor.user.username = keycloak_user.get('username', doctor.keycloak_id)
                doctor.user.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Doctor updated: Dr. {doctor.user.first_name} {doctor.user.last_name}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to sync doctor {doctor.id}: {e}'))

        # Sync all patients
        for patient in Patient.objects.all():
            try:
                user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{patient.keycloak_id}"
                response = requests.get(user_url, headers=headers)
                response.raise_for_status()
                keycloak_user = response.json()
                
                # Update Django user
                patient.user.first_name = keycloak_user.get('firstName', '')
                patient.user.last_name = keycloak_user.get('lastName', '')
                patient.user.email = keycloak_user.get('email', '')
                patient.user.username = keycloak_user.get('username', patient.keycloak_id)
                patient.user.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Patient updated: {patient.user.first_name} {patient.user.last_name}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to sync patient {patient.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Synchronization complete!'))
