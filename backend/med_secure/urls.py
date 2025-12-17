from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    DoctorListView, DoctorDetailView,
    PatientViewSet, MedicalFileViewSet,
    DoctorPatientRequestViewSet, PatientListView,
    FileActionRequestViewSet
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'files', MedicalFileViewSet, basename='file')
router.register(r'requests', DoctorPatientRequestViewSet, basename='request')
router.register(r'file-requests', FileActionRequestViewSet, basename='file-request')

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Doctor endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    
    # Patient endpoints
    path('all-patients/', PatientListView.as_view(), name='all-patients'),
    
    # Include router URLs (patients, files, requests, and file-requests)
    path('', include(router.urls)),
]