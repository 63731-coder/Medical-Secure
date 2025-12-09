"""
Keycloak Authentication Backend for Django REST Framework
Validates JWT tokens from Keycloak and syncs users to Django
"""
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User
from django.conf import settings
from jose import jwt, JWTError
import requests
from .models import Doctor, Patient


class KeycloakAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that validates Keycloak JWT tokens
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode and validate JWT
            decoded_token = self.validate_token(token)
            
            # Get or create Django user from token
            user = self.get_or_create_user(decoded_token)
            
            return (user, token)
        
        except JWTError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def validate_token(self, token):
        """
        Validate JWT token with Keycloak public key
        """
        # Get public key from Keycloak
        public_key = self.get_keycloak_public_key()
        
        # Decode and validate token
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=settings.KEYCLOAK_CLIENT_ID,
            options={
                'verify_signature': True,
                'verify_aud': True,
                'verify_exp': True,
            }
        )
        
        return decoded_token
    
    def get_keycloak_public_key(self):
        """
        Fetch Keycloak realm public key
        Cache it to avoid repeated requests
        """
        if hasattr(settings, '_KEYCLOAK_PUBLIC_KEY'):
            return settings._KEYCLOAK_PUBLIC_KEY
        
        # Fetch from Keycloak
        certs_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        response = requests.get(certs_url)
        response.raise_for_status()
        
        jwks = response.json()
        
        # Extract first public key (RS256)
        key_data = jwks['keys'][0]
        
        # Convert to PEM format
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        from jose.backends import RSAKey
        
        rsa_key = RSAKey(key_data, algorithm='RS256')
        public_key = rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Cache it
        settings._KEYCLOAK_PUBLIC_KEY = public_key
        
        return public_key
    
    def get_or_create_user(self, decoded_token):
        """
        Get or create Django user from Keycloak token
        Sync user attributes and roles
        """
        # Extract user info from token
        username = decoded_token.get('preferred_username')
        email = decoded_token.get('email', '')
        first_name = decoded_token.get('given_name', '')
        last_name = decoded_token.get('family_name', '')
        
        # Get user roles from token
        realm_access = decoded_token.get('realm_access', {})
        roles = realm_access.get('roles', [])
        
        # Get or create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        # Update user info if not created
        if not created:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        
        # Create profile based on roles
        if 'patient' in roles and not hasattr(user, 'patient_profile'):
            # Get date_of_birth from token custom attributes
            date_of_birth = decoded_token.get('date_of_birth', '2000-01-01')
            Patient.objects.create(user=user, date_of_birth=date_of_birth)
        
        elif 'doctor' in roles and not hasattr(user, 'doctor_profile'):
            # Get organisation from token custom attributes
            organisation = decoded_token.get('organisation', 'Unknown')
            Doctor.objects.create(user=user, organisation=organisation)
        
        return user


class KeycloakTokenRefresh:
    """
    Helper class to refresh Keycloak access tokens using refresh token
    """
    
    @staticmethod
    def refresh_token(refresh_token):
        """
        Exchange refresh token for new access token
        """
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token refresh failed: {response.text}")
