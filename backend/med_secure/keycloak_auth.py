from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from django.conf import settings
from jose import jwt, JWTError
from jose.backends import RSAKey
import requests

from .models import Doctor, Patient


class KeycloakAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth.startswith("Bearer "):
            return None

        token = auth.split(" ")[1]

        try:
            decoded = self._decode_token(token)
            user = self._sync_user(decoded)
            return user, token
        except JWTError:
            raise exceptions.AuthenticationFailed("Invalid token")

    def _decode_token(self, token):
        key = self._get_public_key(token)
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )

    def _get_public_key(self, token):
        if not hasattr(settings, "_KEYCLOAK_JWKS"):
            url = (
                f"{settings.KEYCLOAK_SERVER_URL}"
                f"/realms/{settings.KEYCLOAK_REALM}"
                f"/protocol/openid-connect/certs"
            )
            settings._KEYCLOAK_JWKS = requests.get(url).json()

        header = jwt.get_unverified_header(token)
        kid = header["kid"]

        for key in settings._KEYCLOAK_JWKS["keys"]:
            if key["kid"] == kid:
                return RSAKey(key, algorithm="RS256")  # Return RSAKey object directly

        raise exceptions.AuthenticationFailed("Public key not found")

    def _sync_user(self, token):
        keycloak_id = token.get("sub")
        username = token.get("preferred_username") or token.get("sub")  # Fallback to sub
        email = token.get("email", "")
        first_name = token.get("given_name", "")
        last_name = token.get("family_name", "")

        if not keycloak_id:
            raise exceptions.AuthenticationFailed("No sub in token")

        # Get or create Django user by keycloak_id (via Patient/Doctor profile)
        # First try to find existing user via Patient or Doctor profile
        from .models import Patient, Doctor
        
        try:
            patient = Patient.objects.get(keycloak_id=keycloak_id)
            user = patient.user
        except Patient.DoesNotExist:
            try:
                doctor = Doctor.objects.get(keycloak_id=keycloak_id)
                user = doctor.user
            except Doctor.DoesNotExist:
                # Create new user if not found
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    }
                )
        
        # Update user info
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        
        user.set_unusable_password()  # Password managed by Keycloak only
        user.save()

        # Extract roles from token
        roles = token.get("realm_access", {}).get("roles", [])

        # Sync Patient profile
        if "patient" in roles:
            patient, patient_created = Patient.objects.get_or_create(
                keycloak_id=keycloak_id,
                defaults={
                    "user": user,
                    "date_of_birth": None  # Will be updated from Keycloak attributes if needed
                },
            )
            # If patient already exists but linked to different user, update it
            if not patient_created and patient.user != user:
                patient.user = user
                patient.save()

        # Sync Doctor profile
        if "doctor" in roles:
            doctor, doctor_created = Doctor.objects.get_or_create(
                keycloak_id=keycloak_id,
                defaults={
                    "user": user,
                    "organisation": "Unknown"
                },
            )
            # If doctor already exists but linked to different user, update it
            if not doctor_created and doctor.user != user:
                doctor.user = user
                doctor.save()

        return user
