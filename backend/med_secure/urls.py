from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorListView, DoctorDetailView,
    PatientViewSet, MedicalFileViewSet,
    DoctorPatientRequestViewSet, PatientListView,
    FileActionRequestViewSet
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

    # Router URLs (patients, files, requests, file-requests)
    path("", include(router.urls)),
]
