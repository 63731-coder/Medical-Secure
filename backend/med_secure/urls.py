from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorListView, DoctorDetailView,
    PatientViewSet, MedicalFileViewSet,
    DoctorPatientRequestViewSet, PatientListView,
    FileActionRequestViewSet, ShareEncryptionKeyView, GetSharedKeyView
)
from .keycloak_views import (
    KeycloakRegisterView,
    KeycloakLoginView,
    KeycloakCallbackView,
    KeycloakRefreshTokenView,
    KeycloakLogoutView,
    KeycloakConfigView,
    CurrentUserView,
)

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'files', MedicalFileViewSet, basename='file')
router.register(r'requests', DoctorPatientRequestViewSet, basename='request')
router.register(r'file-requests', FileActionRequestViewSet, basename='file-request')

urlpatterns = [
    # Keycloak Auth endpoints
    path("auth/config/", KeycloakConfigView.as_view(), name="keycloak-config"),
    path("auth/register/", KeycloakRegisterView.as_view(), name="keycloak-register"),
    path("auth/login/", KeycloakLoginView.as_view(), name="keycloak-login"),
    path("auth/callback/", KeycloakCallbackView.as_view(), name="keycloak-callback"),
    path("auth/refresh/", KeycloakRefreshTokenView.as_view(), name="keycloak-refresh"),
    path("auth/logout/", KeycloakLogoutView.as_view(), name="keycloak-logout"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),

    # Doctors
    path("doctors/", DoctorListView.as_view(), name="doctor-list"),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name="doctor-detail"),
    
    # Patient endpoints
    path('all-patients/', PatientListView.as_view(), name='all-patients'),
    
    # Encryption key sharing
    path('share-key/', ShareEncryptionKeyView.as_view(), name='share-key'),
    path('get-shared-key/', GetSharedKeyView.as_view(), name='get-shared-key'),

    # Router URLs (patients, files, requests, file-requests)
    path("", include(router.urls)),
]
