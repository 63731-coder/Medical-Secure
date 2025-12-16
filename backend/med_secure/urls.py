from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    DoctorListView, DoctorDetailView, AppointmentRequestCreateView,
    PatientViewSet, MedicalFileViewSet, 
    NotificationViewSet, AuditLogViewSet
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'files', MedicalFileViewSet, basename='file')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Doctor endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    
    # Appointment request endpoint
    path('appointments/request/', AppointmentRequestCreateView.as_view(), name='appointment-request'),
    
    # Include router URLs (patients, files, notifications, audit-logs)
    path('', include(router.urls)),
]