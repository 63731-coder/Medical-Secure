"""
Keycloak integration views for OAuth2/OIDC flow
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
import requests


class KeycloakCallbackView(APIView):
    """
    Handle OAuth2 callback from Keycloak
    Exchange authorization code for tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        POST /api/auth/callback/
        Body: {"code": "authorization_code"}
        """
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'error': 'Authorization code required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Exchange code for tokens
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': request.data.get('redirect_uri', 'http://localhost:5173/callback'),
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
        }
        
        try:
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return Response({
                    'access_token': tokens.get('access_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in'),
                    'token_type': tokens.get('token_type'),
                })
            else:
                return Response(
                    {'error': 'Failed to exchange code', 'details': response.text},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KeycloakRefreshTokenView(APIView):
    """
    Refresh access token using refresh token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        POST /api/auth/refresh/
        Body: {"refresh_token": "..."}
        """
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
        }
        
        try:
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return Response({
                    'access_token': tokens.get('access_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in'),
                })
            else:
                return Response(
                    {'error': 'Token refresh failed'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KeycloakLogoutView(APIView):
    """
    Logout from Keycloak and revoke tokens
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/auth/logout/
        Body: {"refresh_token": "..."}
        """
        refresh_token = request.data.get('refresh_token')
        
        if refresh_token:
            # Revoke refresh token in Keycloak
            logout_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
            
            data = {
                'client_id': settings.KEYCLOAK_CLIENT_ID,
                'client_secret': settings.KEYCLOAK_CLIENT_SECRET,
                'refresh_token': refresh_token,
            }
            
            try:
                requests.post(logout_url, data=data)
            except:
                pass  # Best effort logout
        
        return Response({'message': 'Logged out successfully'})


class KeycloakConfigView(APIView):
    """
    Get Keycloak configuration for frontend
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        GET /api/auth/config/
        Returns Keycloak configuration for frontend to initiate OAuth2 flow
        """
        return Response({
            'server_url': settings.KEYCLOAK_SERVER_URL,
            'realm': settings.KEYCLOAK_REALM,
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'auth_url': f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth",
            'token_url': f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token",
            'redirect_uri': 'http://localhost:5173/callback',
        })
