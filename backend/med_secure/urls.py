from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    DoctorListView, DoctorDetailView,
    PatientViewSet, MedicalFileViewSet
)
from .keycloak_views import (
    KeycloakCallbackView, KeycloakRefreshTokenView,
    KeycloakLogoutView, KeycloakConfigView
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'files', MedicalFileViewSet, basename='file')

urlpatterns = [
    # Keycloak OAuth2/OIDC endpoints (NEW)
    path('auth/config/', KeycloakConfigView.as_view(), name='keycloak-config'),
    path('auth/callback/', KeycloakCallbackView.as_view(), name='keycloak-callback'),
    path('auth/refresh/', KeycloakRefreshTokenView.as_view(), name='keycloak-refresh'),
    path('auth/logout/', KeycloakLogoutView.as_view(), name='keycloak-logout'),
    
    # Legacy auth endpoints (keep for now, deprecated)
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Doctor endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    
    # Include router URLs (patients and files)
    path('', include(router.urls)),
]