from django.core.management.base import BaseCommand
from django.conf import settings
from med_secure.models import Doctor, Patient
import requests


class Command(BaseCommand):
    help = 'Remove orphan users (users that no longer exist in Keycloak)'

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
        deleted_count = 0

        # Check patients
        for patient in Patient.objects.all():
            user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{patient.keycloak_id}"
            try:
                response = requests.get(user_url, headers=headers)
                response.raise_for_status()
                # User exists in Keycloak, all good
            except:
                # User doesn't exist in Keycloak, delete from Django
                username = patient.user.username
                django_user = patient.user
                patient.delete()
                django_user.delete()
                self.stdout.write(self.style.WARNING(f'✗ Deleted orphan patient: {username}'))
                deleted_count += 1

        # Check doctors
        for doctor in Doctor.objects.all():
            user_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{doctor.keycloak_id}"
            try:
                response = requests.get(user_url, headers=headers)
                response.raise_for_status()
                # User exists in Keycloak, all good
            except:
                # User doesn't exist in Keycloak, delete from Django
                username = doctor.user.username
                django_user = doctor.user
                doctor.delete()
                django_user.delete()
                self.stdout.write(self.style.WARNING(f'✗ Deleted orphan doctor: {username}'))
                deleted_count += 1

        if deleted_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No orphan users found!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Cleaned up {deleted_count} orphan user(s)'))
