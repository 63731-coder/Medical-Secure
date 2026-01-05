from rest_framework import viewsets, permissions, status, generics, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest, SharedEncryptionKey
from .serializers import (
    DoctorSerializer, PatientSerializer, MedicalFileSerializer, 
    RegisterSerializer, UserSerializer, DoctorPatientRequestSerializer,
    FileActionRequestSerializer, SharedEncryptionKeySerializer
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
            
            # Check if there's a pending request from this doctor
            pending_request = DoctorPatientRequest.objects.filter(
                doctor=doctor,
                patient=patient,
                status='pending'
            ).first()
            
            if pending_request:
                # Approve the existing request
                pending_request.status = 'approved'
                pending_request.save()
                patient.appointed_doctors.add(doctor)
                return Response({'message': 'Doctor request approved and added successfully'})
            else:
                # Direct add by patient (no approval needed)
                patient.appointed_doctors.add(doctor)
                # Create an approved request record for tracking
                DoctorPatientRequest.objects.create(
                    doctor=doctor,
                    patient=patient,
                    requested_by=request.user,
                    status='approved'
                )
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
# DOCTOR-PATIENT REQUEST VIEWS
# ===========================

class DoctorPatientRequestViewSet(viewsets.ModelViewSet):
    """
    Manage doctor-patient relationship requests
    GET /api/requests/ - List requests
    POST /api/requests/ - Create request
    PATCH /api/requests/{id}/ - Approve/reject request
    """
    serializer_class = DoctorPatientRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Patient sees requests for them
        if hasattr(user, 'patient_profile'):
            return DoctorPatientRequest.objects.filter(patient=user.patient_profile)
        
        # Doctor sees requests they initiated
        elif hasattr(user, 'doctor_profile'):
            return DoctorPatientRequest.objects.filter(doctor=user.doctor_profile)
        
        return DoctorPatientRequest.objects.none()
    
    def create(self, request):
        """
        Create a new doctor-patient request
        Doctor initiates: {"patient_id": 1, "action_type": "add" or "remove"}
        Patient initiates: {"doctor_id": 1}
        """
        user = request.user
        
        if hasattr(user, 'doctor_profile'):
            # Doctor initiating request
            patient_id = request.data.get('patient_id')
            action_type = request.data.get('action_type', 'add')
            
            if not patient_id:
                return Response({'error': 'patient_id is required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            if action_type not in ['add', 'remove']:
                return Response({'error': 'action_type must be "add" or "remove"'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                patient = Patient.objects.get(id=patient_id)
                doctor = user.doctor_profile
                
                if action_type == 'add':
                    # Check if relationship already exists
                    if patient.appointed_doctors.filter(id=doctor.id).exists():
                        return Response({'error': 'Already appointed to this patient'}, 
                                      status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check if request already exists
                    existing = DoctorPatientRequest.objects.filter(
                        doctor=doctor,
                        patient=patient,
                        action_type='add',
                        status='pending'
                    ).first()
                    
                    if existing:
                        return Response({'error': 'Request already pending'}, 
                                      status=status.HTTP_400_BAD_REQUEST)
                else:  # remove
                    # Check if relationship exists
                    if not patient.appointed_doctors.filter(id=doctor.id).exists():
                        return Response({'error': 'Not appointed to this patient'}, 
                                      status=status.HTTP_400_BAD_REQUEST)
                    
                    # Check if remove request already exists
                    existing = DoctorPatientRequest.objects.filter(
                        doctor=doctor,
                        patient=patient,
                        action_type='remove',
                        status='pending'
                    ).first()
                    
                    if existing:
                        return Response({'error': 'Remove request already pending'}, 
                                      status=status.HTTP_400_BAD_REQUEST)
                
                # Create request
                req = DoctorPatientRequest.objects.create(
                    doctor=doctor,
                    patient=patient,
                    requested_by=user,
                    action_type=action_type,
                    status='pending'
                )
                
                return Response(
                    DoctorPatientRequestSerializer(req).data,
                    status=status.HTTP_201_CREATED
                )
            except Patient.DoesNotExist:
                return Response({'error': 'Patient not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        elif hasattr(user, 'patient_profile'):
            # Patient initiating request (auto-approve)
            doctor_id = request.data.get('doctor_id')
            if not doctor_id:
                return Response({'error': 'doctor_id is required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                patient = user.patient_profile
                
                # Check if relationship already exists
                if patient.appointed_doctors.filter(id=doctor.id).exists():
                    return Response({'error': 'Doctor already appointed'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                # Create approved request and add doctor
                req = DoctorPatientRequest.objects.create(
                    doctor=doctor,
                    patient=patient,
                    requested_by=user,
                    status='approved'
                )
                patient.appointed_doctors.add(doctor)
                
                return Response(
                    DoctorPatientRequestSerializer(req).data,
                    status=status.HTTP_201_CREATED
                )
            except Doctor.DoesNotExist:
                return Response({'error': 'Doctor not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        return Response({'error': 'Invalid user type'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Patient approves a doctor's request
        POST /api/requests/{id}/approve/
        """
        req = self.get_object()
        
        # Only patient can approve
        if not hasattr(request.user, 'patient_profile'):
            return Response({'error': 'Only patients can approve requests'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if req.patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if req.status != 'pending':
            return Response({'error': 'Request is not pending'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Approve request
        req.status = 'approved'
        req.save()
        
        # Execute action based on action_type
        if req.action_type == 'add':
            req.patient.appointed_doctors.add(req.doctor)
        elif req.action_type == 'remove':
            req.patient.appointed_doctors.remove(req.doctor)
        
        return Response({
            'message': f'Request {req.action_type} approved',
            'request': DoctorPatientRequestSerializer(req).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Patient rejects a doctor's request
        POST /api/requests/{id}/reject/
        """
        req = self.get_object()
        
        # Only patient can reject
        if not hasattr(request.user, 'patient_profile'):
            return Response({'error': 'Only patients can reject requests'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if req.patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if req.status != 'pending':
            return Response({'error': 'Request is not pending'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        req.status = 'rejected'
        req.save()
        
        return Response({
            'message': 'Request rejected',
            'request': DoctorPatientRequestSerializer(req).data
        })


class PatientListView(generics.ListAPIView):
    """
    List all patients (for doctors to search and add)
    GET /api/all-patients/
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only doctors can see all patients
        if hasattr(self.request.user, 'doctor_profile'):
            return Patient.objects.all()
        return Patient.objects.none()


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
            queryset = MedicalFile.objects.filter(patient=user.patient_profile)
        
        # Doctor sees files of appointed patients
        elif hasattr(user, 'doctor_profile'):
            queryset = MedicalFile.objects.filter(
                patient__appointed_doctors=user.doctor_profile
            )
        else:
            # User has no profile - return empty queryset
            queryset = MedicalFile.objects.none()
        
        # Filter by patient_id if provided (for doctors viewing specific patient)
        patient_id = self.request.query_params.get('patient_id')
        if patient_id and hasattr(user, 'doctor_profile'):
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Handle file upload
        - Patient: immediate upload
        - Doctor: create pending request for patient approval
        """
        user = self.request.user
        
        # Debug: log what we received
        print(f"[DEBUG] File upload - User: {user.username}, Type: {hasattr(user, 'patient_profile')}")
        print(f"[DEBUG] Request data keys: {self.request.data.keys()}")
        print(f"[DEBUG] Has encrypted_name: {'encrypted_name' in self.request.data}")
        
        # If patient uploads for themselves
        if hasattr(user, 'patient_profile'):
            try:
                print(f"[DEBUG] Encrypted metadata - encrypted_name present: {'encrypted_name' in self.request.data}")
                
                # Save with only the foreign keys - encrypted fields are already in serializer.validated_data
                serializer.save(
                    patient=user.patient_profile,
                    uploaded_by=user
                )
            except Exception as e:
                print(f"[ERROR] Upload failed: {str(e)}")
                import traceback
                traceback.print_exc()
                raise drf_serializers.ValidationError(
                    f"Failed to save file: {str(e)}"
                )
        
        # If doctor uploads - create pending request
        elif hasattr(user, 'doctor_profile'):
            patient_id = self.request.data.get('patient_id')
            if not patient_id:
                raise drf_serializers.ValidationError(
                    "patient_id is required for doctor uploads"
                )
            
            try:
                patient = Patient.objects.get(id=patient_id)
                
                # Verify doctor is appointed to this patient
                if not patient.appointed_doctors.filter(id=user.doctor_profile.id).exists():
                    raise permissions.PermissionDenied(
                        "You are not appointed to this patient"
                    )
                
                # Create pending request instead of immediate upload
                file_obj = self.request.FILES.get('file')
                file_name = self.request.data.get('name', '')
                file_description = self.request.data.get('description', '')
                
                # Get encrypted metadata
                encrypted_file_name = self.request.data.get('encrypted_file_name')
                encrypted_file_description = self.request.data.get('encrypted_file_description')
                encrypted_file_date = self.request.data.get('encrypted_file_date')
                
                FileActionRequest.objects.create(
                    patient=patient,
                    doctor=user.doctor_profile,
                    action_type='upload',
                    file_data=file_obj,
                    file_name=file_name,
                    file_description=file_description,
                    encrypted_file_name=encrypted_file_name,
                    encrypted_file_description=encrypted_file_description,
                    encrypted_file_date=encrypted_file_date,
                    status='pending'
                )
                
                raise drf_serializers.ValidationError({
                    'pending': True,
                    'message': 'Upload request sent to patient for approval'
                })
                
            except Patient.DoesNotExist:
                raise drf_serializers.ValidationError("Patient not found")
        else:
            raise drf_serializers.ValidationError(
                "User must have either a patient or doctor profile"
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete medical file
        - Patient: immediate delete
        - Doctor: create pending request for patient approval
        """
        medical_file = self.get_object()
        
        # Patient can delete their files immediately
        if hasattr(request.user, 'patient_profile'):
            if medical_file.patient != request.user.patient_profile:
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
            return super().destroy(request, *args, **kwargs)
        
        # Doctor must request deletion
        elif hasattr(request.user, 'doctor_profile'):
            # Verify doctor has access to this patient
            if not medical_file.patient.appointed_doctors.filter(
                id=request.user.doctor_profile.id
            ).exists():
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Create pending delete request
            FileActionRequest.objects.create(
                patient=medical_file.patient,
                doctor=request.user.doctor_profile,
                action_type='delete',
                target_file=medical_file,
                file_name=medical_file.name,
                status='pending'
            )
            
            return Response({
                'pending': True,
                'message': 'Delete request sent to patient for approval'
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
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
    
    @action(detail=True, methods=['put', 'patch'])
    def edit(self, request, pk=None):
        """
        Edit/update a medical file
        - Patient: immediate update
        - Doctor: create pending request for patient approval
        PUT/PATCH /api/files/{id}/edit/
        """
        medical_file = self.get_object()
        user = request.user
        
        # Patient can edit immediately
        if hasattr(user, 'patient_profile'):
            if medical_file.patient != user.patient_profile:
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Update file
            if 'file' in request.FILES:
                medical_file.file = request.FILES['file']
            if 'name' in request.data:
                medical_file.name = request.data['name']
            if 'description' in request.data:
                medical_file.description = request.data['description']
            
            # Update encrypted metadata
            if 'encrypted_name' in request.data:
                medical_file.encrypted_name = request.data['encrypted_name']
            if 'encrypted_description' in request.data:
                medical_file.encrypted_description = request.data['encrypted_description']
            if 'encrypted_date' in request.data:
                medical_file.encrypted_date = request.data['encrypted_date']
            
            medical_file.save()
            serializer = MedicalFileSerializer(medical_file)
            return Response(serializer.data)
        
        # Doctor must request edit
        elif hasattr(user, 'doctor_profile'):
            # Verify doctor has access
            if not medical_file.patient.appointed_doctors.filter(
                id=user.doctor_profile.id
            ).exists():
                return Response({'error': 'Permission denied'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Create pending edit request
            file_obj = request.FILES.get('file')
            file_name = request.data.get('name', medical_file.name)
            file_description = request.data.get('description', medical_file.description)
            
            # Get encrypted metadata
            encrypted_file_name = request.data.get('encrypted_file_name')
            encrypted_file_description = request.data.get('encrypted_file_description')
            encrypted_file_date = request.data.get('encrypted_file_date')
            
            FileActionRequest.objects.create(
                patient=medical_file.patient,
                doctor=user.doctor_profile,
                action_type='edit',
                target_file=medical_file,
                file_data=file_obj,
                file_name=file_name,
                file_description=file_description,
                encrypted_file_name=encrypted_file_name,
                encrypted_file_description=encrypted_file_description,
                encrypted_file_date=encrypted_file_date,
                status='pending'
            )
            
            return Response({
                'pending': True,
                'message': 'Edit request sent to patient for approval'
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Permission denied'}, 
                       status=status.HTTP_403_FORBIDDEN)


# ===========================
# FILE ACTION REQUEST VIEWS
# ===========================

class FileActionRequestViewSet(viewsets.ModelViewSet):
    """
    Manage file action requests (upload, edit, delete) by doctors
    GET /api/file-requests/ - List requests
    POST /api/file-requests/{id}/approve/ - Approve request
    POST /api/file-requests/{id}/reject/ - Reject request
    """
    serializer_class = FileActionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Patient sees requests for their files
        if hasattr(user, 'patient_profile'):
            return FileActionRequest.objects.filter(patient=user.patient_profile)
        
        # Doctor sees their own requests
        elif hasattr(user, 'doctor_profile'):
            return FileActionRequest.objects.filter(doctor=user.doctor_profile)
        
        return FileActionRequest.objects.none()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Patient approves a file action request
        POST /api/file-requests/{id}/approve/
        """
        action_request = self.get_object()
        
        # Only patient can approve
        if not hasattr(request.user, 'patient_profile'):
            return Response({'error': 'Only patients can approve requests'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if action_request.patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if action_request.status != 'pending':
            return Response({'error': 'Request is not pending'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Approve and execute the action
        action_request.status = 'approved'
        action_request.save()
        
        try:
            action_request.execute_action()
            return Response({
                'message': 'Request approved and executed',
                'request': FileActionRequestSerializer(action_request).data
            })
        except Exception as e:
            action_request.status = 'pending'
            action_request.save()
            return Response({
                'error': f'Failed to execute action: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Patient rejects a file action request
        POST /api/file-requests/{id}/reject/
        """
        action_request = self.get_object()
        
        # Only patient can reject
        if not hasattr(request.user, 'patient_profile'):
            return Response({'error': 'Only patients can reject requests'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if action_request.patient.user != request.user:
            return Response({'error': 'Permission denied'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if action_request.status != 'pending':
            return Response({'error': 'Request is not pending'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        action_request.status = 'rejected'
        action_request.save()
        
        # Clean up pending file if it was an upload/edit
        if action_request.file_data:
            action_request.file_data.delete()
        
        return Response({
            'message': 'Request rejected',
            'request': FileActionRequestSerializer(action_request).data
        })


# ===========================
# SHARED ENCRYPTION KEY VIEWS
# ===========================

class ShareEncryptionKeyView(APIView):
    """
    Patient shares their encryption key with a doctor
    POST /api/share-key/
    Body: {
        "doctor_id": 1,
        "encrypted_key": "base64_encrypted_key_string"
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Only patients can share keys
        if not hasattr(request.user, 'patient_profile'):
            return Response({'error': 'Only patients can share encryption keys'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        patient = request.user.patient_profile
        doctor_id = request.data.get('doctor_id')
        encrypted_key = request.data.get('encrypted_key')
        
        if not doctor_id or not encrypted_key:
            return Response({'error': 'doctor_id and encrypted_key are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Check if doctor is appointed
        if doctor not in patient.appointed_doctors.all():
            return Response({'error': 'Doctor is not appointed to this patient'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Create or update shared key
        shared_key, created = SharedEncryptionKey.objects.update_or_create(
            patient=patient,
            doctor=doctor,
            defaults={'encrypted_key': encrypted_key}
        )
        
        return Response({
            'message': 'Encryption key shared successfully',
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class GetSharedKeyView(APIView):
    """
    Doctor retrieves shared encryption key from a patient
    GET /api/get-shared-key/?patient_id=1
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Only doctors can retrieve shared keys
        if not hasattr(request.user, 'doctor_profile'):
            return Response({'error': 'Only doctors can retrieve shared keys'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        doctor = request.user.doctor_profile
        patient_id = request.query_params.get('patient_id')
        
        if not patient_id:
            return Response({'error': 'patient_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Check if doctor is appointed to this patient
        if doctor not in patient.appointed_doctors.all():
            return Response({'error': 'You are not appointed to this patient'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Get shared key
        try:
            shared_key = SharedEncryptionKey.objects.get(patient=patient, doctor=doctor)
            return Response({
                'encrypted_key': shared_key.encrypted_key,
                'patient_id': patient.id,
                'patient_username': patient.user.username
            })
        except SharedEncryptionKey.DoesNotExist:
            return Response({'error': 'No shared key found for this patient'}, 
                          status=status.HTTP_404_NOT_FOUND)

