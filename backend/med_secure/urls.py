from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorListView, DoctorDetailView, PatientViewSet, MedicalFileViewSet
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
router.register("patients", PatientViewSet, basename="patient")
router.register("files", MedicalFileViewSet, basename="file")

urlpatterns = [
    # Auth endpoints
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

    # Router URLs
    path("", include(router.urls)),
]
