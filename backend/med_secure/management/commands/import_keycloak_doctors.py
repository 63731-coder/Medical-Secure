from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from med_secure.models import Doctor
import requests


class Command(BaseCommand):
    help = 'Import all doctors from Keycloak to Django'

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

        # Get doctor role
        role_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/roles/doctor"
        try:
            role_response = requests.get(role_url, headers=headers)
            role_response.raise_for_status()
            doctor_role = role_response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get doctor role: {e}'))
            return

        # Get all users with doctor role
        users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/roles/doctor/users"
        try:
            users_response = requests.get(users_url, headers=headers)
            users_response.raise_for_status()
            doctor_users = users_response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get doctor users: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {len(doctor_users)} doctors in Keycloak\n'))

        # Import each doctor
        for keycloak_user in doctor_users:
            keycloak_id = keycloak_user['id']
            username = keycloak_user.get('username', keycloak_id)
            email = keycloak_user.get('email', '')
            first_name = keycloak_user.get('firstName', '')
            last_name = keycloak_user.get('lastName', '')

            # Check if doctor already exists
            if Doctor.objects.filter(keycloak_id=keycloak_id).exists():
                self.stdout.write(f'⏭  Dr. {first_name} {last_name} already exists, skipping')
                continue

            try:
                # Create Django user
                django_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                django_user.set_unusable_password()
                django_user.save()

                # Create Doctor profile
                Doctor.objects.create(
                    user=django_user,
                    keycloak_id=keycloak_id,
                    organisation='Unknown'  # Can be updated later
                )

                self.stdout.write(self.style.SUCCESS(
                    f'✓ Imported: Dr. {first_name} {last_name} ({email})'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Failed to import {username}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS('\n✅ Import complete!'))
