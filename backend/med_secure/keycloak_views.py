"""
Keycloak OAuth2 / OIDC integration views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.contrib.auth.models import User
import requests
from .models import Patient, Doctor
from .utils.security_events import log_user_registered


class KeycloakRegisterView(APIView):
    """
    Register a new user in Keycloak and sync to local DB
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        user_type = request.data.get('user_type')  # 'patient' or 'doctor'
        recaptcha_token = request.data.get('recaptcha_token')  # reCAPTCHA v3 token
        
        # Additional fields
        date_of_birth = request.data.get('date_of_birth')  # for patient (encrypted)
        organisation = request.data.get('organisation')  # for doctor (plaintext)
        
        # Encrypted sensitive data (client-side encrypted) - for Django DB
        encrypted_first_name = request.data.get('first_name')  # Encrypted
        encrypted_last_name = request.data.get('last_name')  # Encrypted
        encrypted_date_of_birth = request.data.get('date_of_birth')  # Encrypted
        
        # Plaintext versions for Keycloak only
        plaintext_first_name = request.data.get('plaintext_first_name', '')
        plaintext_last_name = request.data.get('plaintext_last_name', '')

        # Validation
        if not all([username, email, password, user_type]):
            return Response(
                {'error': 'username, email, password, and user_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_type not in ['patient', 'doctor']:
            return Response(
                {'error': 'user_type must be "patient" or "doctor"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ===========================
        # reCAPTCHA v3 Verification
        # ===========================
        if recaptcha_token:
            recaptcha_secret = settings.RECAPTCHA_SECRET_KEY
            recaptcha_url = 'https://www.google.com/recaptcha/api/siteverify'
            
            try:
                recaptcha_response = requests.post(recaptcha_url, data={
                    'secret': recaptcha_secret,
                    'response': recaptcha_token
                })
                recaptcha_result = recaptcha_response.json()
                
                # Check if verification succeeded
                if not recaptcha_result.get('success'):
                    return Response(
                        {'error': 'reCAPTCHA verification failed. Please try again.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check score (v3 only) - should be >= 0.5 for human-like behavior
                score = recaptcha_result.get('score', 0)
                if score < 0.5:
                    return Response(
                        {'error': 'Registration blocked: Bot-like behavior detected.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
            except Exception as e:
                return Response(
                    {'error': 'Failed to verify reCAPTCHA. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'reCAPTCHA token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get admin token for Keycloak API calls
        admin_token = self._get_admin_token()
        if not admin_token:
            return Response(
                {'error': 'Failed to authenticate with Keycloak'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create user in Keycloak
        # Create user payload for Keycloak - use PLAINTEXT
        user_data = {
            'username': username,               # Plaintext for Keycloak auth
            'email': email,                     # Plaintext for Keycloak auth  
            'firstName': plaintext_first_name,  # Plaintext for Keycloak UI
            'lastName': plaintext_last_name,    # Plaintext for Keycloak UI
            'enabled': True,
            'emailVerified': True,
            'credentials': [{
                'type': 'password',
                'value': password,
                'temporary': True  # Force password change (will trigger passkey setup)
            }],
            'requiredActions': ['webauthn-register-passwordless'],  # Force passkey setup
            'realmRoles': [user_type],
            'attributes': {}
        }

        # Add type-specific attributes (NOT encrypted in Keycloak)
        if user_type == 'patient' and encrypted_date_of_birth:
            # Don't store encrypted data in Keycloak - Keycloak is for authentication only
            pass
        elif user_type == 'doctor' and organisation:
            user_data['attributes']['organisation'] = [organisation]

        # Create user in Keycloak
        create_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        response = requests.post(create_url, json=user_data, headers=headers)

        if response.status_code == 409:
            return Response(
                {'error': 'User already exists'},
                status=status.HTTP_409_CONFLICT
            )
        
        if response.status_code not in [201, 204]:
            return Response(
                {'error': 'Failed to create user in Keycloak', 'details': response.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get the created user's Keycloak ID
        keycloak_user = self._get_keycloak_user_by_username(username, admin_token)
        if not keycloak_user:
            return Response(
                {'error': 'User created but could not retrieve Keycloak ID'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        keycloak_id = keycloak_user['id']

        # Assign role to user
        self._assign_role_to_user(keycloak_id, user_type, admin_token)

        # Create user in local database
        try:
            # Ensure encrypted names are not empty/None
            safe_first_name = encrypted_first_name if encrypted_first_name else ''
            safe_last_name = encrypted_last_name if encrypted_last_name else ''
            
            # Store encrypted data for BOTH patients and doctors in User model
            django_user = User.objects.create_user(
                username=username,         # Plaintext (for auth)
                email=email,               # Plaintext (for auth)
                first_name=safe_first_name,  # Encrypted (same for patients and doctors)
                last_name=safe_last_name     # Encrypted (same for patients and doctors)
            )
            
            django_user.set_unusable_password()  # Password managed by Keycloak
            django_user.save()

            # Create profile based on user type
            if user_type == 'patient':
                Patient.objects.create(
                    user=django_user,
                    keycloak_id=keycloak_id,
                    date_of_birth=encrypted_date_of_birth or '',  # Encrypted (or empty)
                    first_name=safe_first_name,                   # Encrypted (or empty)
                    last_name=safe_last_name                      # Encrypted (or empty)
                )
            else:  # doctor
                Doctor.objects.create(
                    user=django_user,
                    keycloak_id=keycloak_id,
                    organisation=organisation or ''  # Plaintext (or empty)
                )
            
            # Log user registration
            log_user_registered(
                user_id=django_user.id,
                username=username,
                user_type=user_type,
                keycloak_id=keycloak_id
            )

            return Response({
                'message': 'User registered successfully',
                'username': username,
                'user_type': user_type,
                'keycloak_id': keycloak_id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'User created in Keycloak but failed to sync to database: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_admin_token(self):
        """Get admin access token from Keycloak"""
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin123',  # From docker-compose
        }
        try:
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                return response.json()['access_token']
        except Exception:
            pass
        return None

    def _get_keycloak_user_by_username(self, username, admin_token):
        """Get Keycloak user by username"""
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users"
        headers = {'Authorization': f'Bearer {admin_token}'}
        params = {'username': username, 'exact': 'true'}
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
        except Exception:
            pass
        return None

    def _assign_role_to_user(self, user_id, role_name, admin_token):
        """Assign a realm role to a user"""
        # Get role details
        roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/roles/{role_name}"
        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        
        try:
            print(f"[DEBUG] Getting role {role_name} from {roles_url}")
            role_response = requests.get(roles_url, headers=headers)
            print(f"[DEBUG] Role fetch status: {role_response.status_code}")
            
            if role_response.status_code != 200:
                print(f"[ERROR] Failed to get role: {role_response.text}")
                return False
            
            role = role_response.json()
            print(f"[DEBUG] Role found: {role}")
            
            # Assign role to user
            assign_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{user_id}/role-mappings/realm"
            print(f"[DEBUG] Assigning role to user at {assign_url}")
            assign_response = requests.post(assign_url, json=[role], headers=headers)
            print(f"[DEBUG] Role assignment status: {assign_response.status_code}")
            print(f"[DEBUG] Role assignment response: {assign_response.text}")
            return True
        except Exception as e:
            print(f"[ERROR] Exception in role assignment: {str(e)}")
            return False


class KeycloakCallbackView(APIView):
    """
    Handle OAuth2 Authorization Code callback from Keycloak
    
    This is the primary authentication endpoint for WebAuthn/Passwordless flow.
    After user authenticates with WebAuthn on Keycloak, they are redirected here
    with an authorization code that we exchange for tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')

        if not code:
            return Response({'error': 'Authorization code required'},
                            status=status.HTTP_400_BAD_REQUEST)

        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
            'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
        }

        try:
            print(f"[DEBUG] Token URL: {token_url}")
            print(f"[DEBUG] Request data: {data}")
            response = requests.post(token_url, data=data)
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response text: {response.text}")

            if response.status_code != 200:
                return Response({
                    'error': 'Token exchange failed', 
                    'details': response.text
                }, status=status.HTTP_400_BAD_REQUEST)

            tokens = response.json()
            
            # Return tokens to frontend
            return Response({
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'expires_in': tokens['expires_in'],
                'token_type': tokens['token_type'],
            })
            
        except Exception as e:
            return Response({
                'error': f'Callback processing failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KeycloakRefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'error': 'Refresh token required'},
                            status=status.HTTP_400_BAD_REQUEST)

        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
        }

        response = requests.post(token_url, data=data)

        if response.status_code != 200:
            return Response({'error': 'Token refresh failed'},
                            status=status.HTTP_401_UNAUTHORIZED)

        tokens = response.json()
        return Response(tokens)


class KeycloakLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if refresh_token:
            logout_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
            requests.post(logout_url, data={
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
                'refresh_token': refresh_token,
            })

        return Response({'message': 'Logged out'})


class KeycloakLoginView(APIView):
    """
    Direct login with username/password (Resource Owner Password Credentials flow)
    
    ⚠️ DEPRECATED for WebAuthn/Passwordless flow
    This endpoint is kept for backwards compatibility and testing.
    For production with WebAuthn, use the Authorization Code Flow via /auth/config/ 
    and redirect to Keycloak login page.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"

        data = {
            'grant_type': 'password',
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
            'username': username,
            'password': password,
            'scope': 'openid profile email'
        }

        try:
            response = requests.post(token_url, data=data)

            if response.status_code == 200:
                tokens = response.json()
                return Response({
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'expires_in': tokens['expires_in'],
                    'token_type': tokens['token_type'],
                })
            else:
                return Response(
                    {'error': 'Invalid credentials or passwordless flow enabled. Use WebAuthn login.', 
                     'details': response.text},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            return Response(
                {'error': f'Login failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KeycloakConfigView(APIView):
    """
    Returns Keycloak configuration for frontend
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'server_url': settings.KEYCLOAK_SERVER_URL,
            'realm': settings.KEYCLOAK_REALM,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'auth_url': f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth",
            'token_url': f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
            'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
        })


class CurrentUserView(APIView):
    """
    Get current authenticated user's profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Determine user type and get profile
        user_type = None
        profile_data = {}
        encrypted_data = {}
        
        if hasattr(user, 'patient_profile'):
            user_type = 'patient'
            patient = user.patient_profile
            profile_data = {
                'id': patient.id,
                'keycloak_id': patient.keycloak_id,
                'date_of_birth': patient.date_of_birth,
                'appointed_doctors': [
                    {
                        'id': doc.id,
                        'name': f"Dr. {doc.user.first_name} {doc.user.last_name}",
                        'organisation': doc.organisation
                    }
                    for doc in patient.appointed_doctors.all()
                ]
            }
            # Add encrypted data for client-side decryption
            encrypted_data = {
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'date_of_birth': patient.date_of_birth
            }
        elif hasattr(user, 'doctor_profile'):
            user_type = 'doctor'
            doctor = user.doctor_profile
            profile_data = {
                'id': doctor.id,
                'keycloak_id': doctor.keycloak_id,
                'organisation': doctor.organisation,
                'patient_count': doctor.patients.count()
            }
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user_type,
            'profile': profile_data,
            'encrypted_data': encrypted_data
        })
