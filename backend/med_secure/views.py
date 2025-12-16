from rest_framework import viewsets, permissions, status, generics, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile
from .serializers import (
    DoctorSerializer, PatientSerializer, MedicalFileSerializer, 
    RegisterSerializer, UserSerializer
)


# ===========================
# AUTH VIEWS
# ===========================

class RegisterView(generics.CreateAPIView):
    """
    Register new user (patient or doctor)
    POST /api/register/
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate token for immediate login
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login and get auth token
    POST /api/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token, created = Token.objects.get_or_create(user=user)
        
        # Determine user type
        user_type = None
        profile_id = None
        if hasattr(user, 'patient_profile'):
            user_type = 'patient'
            profile_id = user.patient_profile.id
        elif hasattr(user, 'doctor_profile'):
            user_type = 'doctor'
            profile_id = user.doctor_profile.id
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'user_type': user_type,
            'profile_id': profile_id
        })


class LogoutView(generics.GenericAPIView):
    """
    Logout by deleting token
    POST /api/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'}, 
                       status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveAPIView):
    """
    Get current user profile
    GET /api/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request):
        user = request.user
        user_data = UserSerializer(user).data
        
        if hasattr(user, 'patient_profile'):
            try:
                profile = PatientSerializer(user.patient_profile).data
                user_data['profile'] = profile
                user_data['user_type'] = 'patient'
            except Exception as e:
                return Response(
                    {'error': f'Failed to load patient profile: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        elif hasattr(user, 'doctor_profile'):
            try:
                profile = DoctorSerializer(user.doctor_profile).data
                user_data['profile'] = profile
                user_data['user_type'] = 'doctor'
            except Exception as e:
                return Response(
                    {'error': f'Failed to load doctor profile: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'No profile found. User must be either a patient or doctor.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(user_data)


# ===========================
# DOCTOR VIEWS
# ===========================

class DoctorListView(generics.ListAPIView):
    """
    List all doctors (for patients to choose)
    GET /api/doctors/
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]


class DoctorDetailView(generics.RetrieveAPIView):
    """
    Get doctor details
    GET /api/doctors/{id}/
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]


# ===========================
# PATIENT VIEWS
# ===========================

class PatientViewSet(viewsets.ModelViewSet):
    """
    Patient CRUD operations
    GET /api/patients/ - List patients
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Patient sees only their own profile
        if hasattr(user, 'patient_profile'):
            return Patient.objects.filter(user=user)
        
        # Doctor sees their appointed patients
        elif hasattr(user, 'doctor_profile'):
            return Patient.objects.filter(appointed_doctors=user.doctor_profile)
        
        return Patient.objects.none()
    
    @action(detail=True, methods=['post'])
    def add_doctor(self, request, pk=None):
        """
        Patient adds a doctor to their list
        POST /api/patients/{id}/add-doctor/
        Body: {"doctor_id": 1}
        """
        patient = self.get_object()
        
        # Only patient can add doctors to their own profile
        if patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        doctor_id = request.data.get('doctor_id')
        if not doctor_id:
            return Response({'error': 'doctor_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            patient.appointed_doctors.add(doctor)
            return Response({'message': 'Doctor added successfully'})
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path='remove-doctor/(?P<doctor_id>[^/.]+)')
    def remove_doctor(self, request, pk=None, doctor_id=None):
        """
        Patient removes a doctor from their list
        DELETE /api/patients/{id}/remove-doctor/{doctor_id}/
        """
        patient = self.get_object()
        
        # Only patient can remove doctors from their own profile
        if patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            patient.appointed_doctors.remove(doctor)
            return Response({'message': 'Doctor removed successfully'})
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, 
                          status=status.HTTP_404_NOT_FOUND)


# ===========================
# MEDICAL FILES VIEWS
# ===========================

class MedicalFileViewSet(viewsets.ModelViewSet):
    """
    Medical files CRUD
    GET /api/files/ - List files
    POST /api/files/ - Upload file
    GET /api/files/{id}/ - Download file
    DELETE /api/files/{id}/ - Delete file
    """
    serializer_class = MedicalFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Patient sees their own files
        if hasattr(user, 'patient_profile'):
            return MedicalFile.objects.filter(patient=user.patient_profile)
        
        # Doctor sees files of appointed patients
        elif hasattr(user, 'doctor_profile'):
            return MedicalFile.objects.filter(
                patient__appointed_doctors=user.doctor_profile
            )
        
        return MedicalFile.objects.none()
    
    def perform_create(self, serializer):
        """
        Handle file upload
        Attach file to patient and track uploader
        """
        user = self.request.user
        
        # If patient uploads for themselves
        if hasattr(user, 'patient_profile'):
            serializer.save(
                patient=user.patient_profile,
                uploaded_by=user
            )
        
        # If doctor uploads (patient_id must be provided)
        elif hasattr(user, 'doctor_profile'):
            patient_id = self.request.data.get('patient_id')
            if not patient_id:
                raise serializers.ValidationError(
                    "patient_id is required for doctor uploads"
                )
            
            try:
                patient = Patient.objects.get(id=patient_id)
                
                # Verify doctor is appointed to this patient
                if not patient.appointed_doctors.filter(id=user.doctor_profile.id).exists():
                    raise permissions.PermissionDenied(
                        "You are not appointed to this patient"
                    )
                
                serializer.save(patient=patient, uploaded_by=user)
            except Patient.DoesNotExist:
                raise serializers.ValidationError("Patient not found")
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete medical file
        Only patient can delete their own files
        """
        medical_file = self.get_object()
        
        # Only patient can delete their files
        if hasattr(request.user, 'patient_profile'):
            if medical_file.patient != request.user.patient_profile:
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Only patients can delete files'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download encrypted file
        GET /api/medical-files/{id}/download/
        Returns the encrypted file blob (client will decrypt)
        """
        from django.http import FileResponse
        
        medical_file = self.get_object()
        
        # Security check: user has access to this file
        if hasattr(request.user, 'patient_profile'):
            if medical_file.patient != request.user.patient_profile:
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
        elif hasattr(request.user, 'doctor_profile'):
            if not medical_file.patient.appointed_doctors.filter(
                id=request.user.doctor_profile.id
            ).exists():
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
        
        # Return file (already encrypted)
        response = FileResponse(medical_file.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{medical_file.file.name}"'
        return response

