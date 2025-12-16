from rest_framework import viewsets, permissions, status, generics, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Doctor, Patient, MedicalFile, AppointmentRequest, FileActionRequest, Notification, AuditLog
from .serializers import (
    DoctorSerializer, PatientSerializer, MedicalFileSerializer, 
    RegisterSerializer, UserSerializer, AppointmentRequestSerializer, 
    FileActionRequestSerializer, NotificationSerializer, AuditLogSerializer
)
from .permissions import (
    IsPatientOwner, IsAppointedDoctor, IsDoctor, IsPatient,
    CanViewMedicalFile, CanModifyMedicalFile, CanApproveRequest
)
from .utils import log_action, create_notification, get_client_ip, get_user_agent


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
            profile = PatientSerializer(user.patient_profile).data
            user_data['profile'] = profile
            user_data['user_type'] = 'patient'
        elif hasattr(user, 'doctor_profile'):
            profile = DoctorSerializer(user.doctor_profile).data
            user_data['profile'] = profile
            user_data['user_type'] = 'doctor'
        
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


class AppointmentRequestCreateView(APIView):
    """Doctor initiates a request to be appointed to a patient
    POST /api/appointments/request/
    Body: {"patient_id": <id>}
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if not hasattr(user, 'doctor_profile'):
            return Response({'error': 'Only doctors may create appointment requests'}, status=status.HTTP_403_FORBIDDEN)

        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

        # If already appointed, nothing to do
        if patient.appointed_doctors.filter(id=user.doctor_profile.id).exists():
            return Response({'error': 'You are already appointed to this patient'}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate pending requests
        existing = AppointmentRequest.objects.filter(doctor=user.doctor_profile, patient=patient, status=AppointmentRequest.STATUS_PENDING).first()
        if existing:
            return Response({'error': 'There is already a pending request'}, status=status.HTTP_400_BAD_REQUEST)

        ar = AppointmentRequest.objects.create(doctor=user.doctor_profile, patient=patient)
        
        # Create notification for patient
        create_notification(
            recipient=patient.user,
            sender=user,
            notification_type='appointment_request',
            title='New Appointment Request',
            message=f'Dr. {user.get_full_name()} from {user.doctor_profile.organisation} requests to be your doctor',
            appointment_request=ar
        )
        
        # Log the action
        log_action(
            user=user,
            action='appointment_request',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            patient=patient,
            details={'patient_id': patient.id}
        )
        
        serializer = AppointmentRequestSerializer(ar)
        return Response({'message': 'Appointment request created', 'request': serializer.data}, status=status.HTTP_201_CREATED)


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
            # Patient explicitly adds a doctor (immediate)
            patient.appointed_doctors.add(doctor)
            return Response({'message': 'Doctor added successfully'})
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='appointment-requests')
    def appointment_requests(self, request, pk=None):
        """Patient lists pending appointment requests"""
        patient = self.get_object()
        if patient.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        qs = patient.appointment_requests.filter(status=AppointmentRequest.STATUS_PENDING)
        serializer = AppointmentRequestSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='appointment-requests/(?P<request_id>[^/.]+)/respond')
    def respond_appointment_request(self, request, pk=None, request_id=None):
        """Patient approves or rejects an appointment request"""
        patient = self.get_object()
        if patient.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action not in ('approve', 'reject'):
            return Response({'error': 'action must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            req = AppointmentRequest.objects.get(id=request_id, patient=patient)
        except AppointmentRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            req.status = AppointmentRequest.STATUS_APPROVED
            # add the doctor to patient's appointed_doctors
            patient.appointed_doctors.add(req.doctor)
            notification_type = 'request_approved'
            title = 'Appointment Request Approved'
            message = f'Patient {patient.user.get_full_name()} has approved your appointment request'
        else:
            req.status = AppointmentRequest.STATUS_REJECTED
            notification_type = 'request_rejected'
            title = 'Appointment Request Rejected'
            message = f'Patient {patient.user.get_full_name()} has rejected your appointment request'

        req.save()
        
        # Notify the doctor
        create_notification(
            recipient=req.doctor.user,
            sender=request.user,
            notification_type=notification_type,
            title=title,
            message=message,
            appointment_request=req
        )
        
        # Log the action
        log_action(
            user=request.user,
            action='approve_request' if action == 'approve' else 'reject_request',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            patient=patient,
            details={'request_id': req.id, 'doctor_id': req.doctor.id}
        )
        
        return Response({'message': f'Request {action}d'})
    
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
        
        # If patient uploads for themselves -> immediate storage
        if hasattr(user, 'patient_profile'):
            serializer.save(
                patient=user.patient_profile,
                uploaded_by=user,
                approved=True
            )

        # If doctor uploads -> deferred storage: create FileActionRequest with the uploaded file
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

                # Build FileActionRequest storing the uploaded file until patient approval
                pending_file = self.request.FILES.get('file')
                name = self.request.data.get('name')
                description = self.request.data.get('description', '')

                far = FileActionRequest.objects.create(
                    medical_file=None,
                    requested_by=user,
                    target_patient=patient,
                    action_type=FileActionRequest.ACTION_UPLOAD,
                    status=FileActionRequest.STATUS_PENDING,
                    file=pending_file,
                    name=name,
                    description=description
                )
                
                # Create notification for patient
                create_notification(
                    recipient=patient.user,
                    sender=user,
                    notification_type='file_action_request',
                    title='New File Upload Request',
                    message=f'Dr. {user.get_full_name()} wants to upload file: {name}',
                    file_action_request=far
                )

                serializer = FileActionRequestSerializer(far, context={'request': request})
                return Response({'message': 'Upload pending patient approval', 'request': serializer.data}, status=status.HTTP_201_CREATED)
            except Patient.DoesNotExist:
                raise serializers.ValidationError("Patient not found")

    def update(self, request, *args, **kwargs):
        """Secure update: patient may modify directly; doctor modifications create a pending FileActionRequest."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        # Patient may modify directly
        if hasattr(user, 'patient_profile') and instance.patient == user.patient_profile:
            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)

        # Doctor modifications: validate appointed status then create a pending request
        if hasattr(user, 'doctor_profile'):
            if not instance.patient.appointed_doctors.filter(id=user.doctor_profile.id).exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            # Apply changes but mark as unapproved and create FileActionRequest
            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
            serializer.is_valid(raise_exception=True)
            # save changes but ensure approved=False
            mf = serializer.save(approved=False)
            far = FileActionRequest.objects.create(
                medical_file=mf,
                requested_by=user,
                action_type=FileActionRequest.ACTION_MODIFY,
                status=FileActionRequest.STATUS_PENDING,
            )
            
            # Create notification for patient
            create_notification(
                recipient=mf.patient.user,
                sender=user,
                notification_type='file_action_request',
                title='File Modification Request',
                message=f'Dr. {user.get_full_name()} wants to modify file: {mf.name}',
                file_action_request=far
            )
            
            return Response({'message': 'Modification requested, pending patient approval', 'request_id': far.id})

        return Response({'error': 'Only the patient or appointed doctors may modify files'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """Serve file content only after strict permission checks. Doctors can download only if file approved."""
        mf = self.get_object()
        user = request.user

        # Patient always allowed
        if hasattr(user, 'patient_profile') and mf.patient == user.patient_profile:
            return self._file_response(mf)

        # Uploader may access their own upload
        if mf.uploaded_by == user:
            return self._file_response(mf)

        # Appointed doctor allowed only if file approved
        if hasattr(user, 'doctor_profile') and mf.patient.appointed_doctors.filter(id=user.doctor_profile.id).exists():
            if mf.approved:
                return self._file_response(mf)
            else:
                return Response({'error': 'File not yet approved by patient'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    def _file_response(self, medical_file):
        # Use Django's FileResponse to stream file from storage, preventing public URL exposure
        from django.http import FileResponse, Http404
        try:
            f = medical_file.file.open('rb')
        except Exception:
            raise Http404

        response = FileResponse(f, as_attachment=True, filename=medical_file.name)
        return response
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete medical file
        Deletion rules:
        - Patient can delete their own files directly
        - Doctor can request deletion (creates FileActionRequest) which patient must approve
        """
        medical_file = self.get_object()
        
        # Only patient can delete their files
        if hasattr(request.user, 'patient_profile'):
            if medical_file.patient != request.user.patient_profile:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            # Patient may delete directly
            return super().destroy(request, *args, **kwargs)
        
        # If doctor requests deletion, create a FileActionRequest (deferred action)
        elif hasattr(request.user, 'doctor_profile'):
            # verify doctor appointed
            if not medical_file.patient.appointed_doctors.filter(id=request.user.doctor_profile.id).exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            far = FileActionRequest.objects.create(
                medical_file=medical_file,
                requested_by=request.user,
                action_type=FileActionRequest.ACTION_DELETE,
                status=FileActionRequest.STATUS_PENDING
            )
            
            # Create notification for patient
            create_notification(
                recipient=medical_file.patient.user,
                sender=request.user,
                notification_type='file_action_request',
                title='File Deletion Request',
                message=f'Dr. {request.user.get_full_name()} wants to delete file: {medical_file.name}',
                file_action_request=far
            )
            
            serializer = FileActionRequestSerializer(far, context={'request': request})
            return Response({'message': 'Deletion requested, pending patient approval', 'request': serializer.data})

        else:
            return Response({'error': 'Only patients or appointed doctors may request deletions'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='pending-file-actions')
    def pending_file_actions(self, request):
        """List pending file action requests for the current patient"""
        user = request.user
        if not hasattr(user, 'patient_profile'):
            return Response({'error': 'Only patients can list pending file actions'}, status=status.HTTP_403_FORBIDDEN)

        qs = FileActionRequest.objects.filter(medical_file__patient=user.patient_profile, status=FileActionRequest.STATUS_PENDING)
        serializer = FileActionRequestSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='respond-file-action')
    def respond_file_action(self, request):
        """Patient approves or rejects a file action request"""
        user = request.user
        if not hasattr(user, 'patient_profile'):
            return Response({'error': 'Only patients can respond to file actions'}, status=status.HTTP_403_FORBIDDEN)

        req_id = request.data.get('request_id')
        action = request.data.get('action')  # 'approve' or 'reject'
        if not req_id or action not in ('approve', 'reject'):
            return Response({'error': 'request_id and action (approve/reject) are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            far = FileActionRequest.objects.get(id=req_id, medical_file__patient=user.patient_profile)
        except FileActionRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            far.status = FileActionRequest.STATUS_APPROVED
            # apply the action
            if far.action_type == FileActionRequest.ACTION_UPLOAD:
                # create MedicalFile from pending file stored on the request
                mf = MedicalFile.objects.create(
                    patient=user.patient_profile,
                    file=far.file,
                    name=far.name or (far.file.name if far.file else 'unnamed'),
                    description=far.description or '',
                    uploaded_by=far.requested_by,
                    approved=True
                )
                # link request to created medical file for audit
                far.medical_file = mf
                far.save()
            elif far.action_type == FileActionRequest.ACTION_DELETE:
                if far.medical_file:
                    far.medical_file.delete()
            elif far.action_type == FileActionRequest.ACTION_MODIFY:
                # replace contents of target medical_file with pending file
                mf = far.medical_file
                if far.file and mf:
                    mf.file.delete(save=False)
                    mf.file = far.file
                    if far.name:
                        mf.name = far.name
                    if far.description:
                        mf.description = far.description
                    mf.approved = True
                    mf.uploaded_by = far.requested_by
                    mf.save()
        else:
            far.status = FileActionRequest.STATUS_REJECTED
            # if upload was rejected, optionally delete the unapproved file
            if far.action_type == FileActionRequest.ACTION_UPLOAD:
                far.medical_file.delete()

        far.save()
        
        # Notify the doctor about the decision
        notification_type = 'request_approved' if action == 'approve' else 'request_rejected'
        title = f'File {far.action_type} Request {action.capitalize()}d'
        message = f'Patient {user.patient_profile.user.get_full_name()} has {action}d your {far.action_type} request for {far.name or "file"}'
        
        create_notification(
            recipient=far.requested_by,
            sender=user,
            notification_type=notification_type,
            title=title,
            message=message,
            file_action_request=far
        )
        
        # Log the action
        log_action(
            user=user,
            action='approve_request' if action == 'approve' else 'reject_request',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            medical_file=far.medical_file,
            patient=user.patient_profile,
            details={'request_id': far.id, 'action_type': far.action_type}
        )
        
        return Response({'message': f'File action {action}d'})


# ===========================
# NOTIFICATION VIEWS
# ===========================

class NotificationViewSet(viewsets.ModelViewSet):
    """
    Manage notifications for the current user
    GET /api/notifications/ - List notifications
    GET /api/notifications/{id}/ - Get notification detail
    POST /api/notifications/{id}/mark-read/ - Mark as read
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users only see their own notifications"""
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read for current user"""
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        updated = notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': f'{updated} notifications marked as read'})
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})


# ===========================
# AUDIT LOG VIEWS
# ===========================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View audit logs (read-only)
    GET /api/audit-logs/ - List audit logs
    GET /api/audit-logs/{id}/ - Get audit log detail
    
    Patients can see logs related to their own records.
    Doctors can see logs for their actions.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter audit logs based on user permissions"""
        user = self.request.user
        
        if hasattr(user, 'patient_profile'):
            # Patients see logs related to their medical records
            return AuditLog.objects.filter(patient=user.patient_profile)
        
        elif hasattr(user, 'doctor_profile'):
            # Doctors see their own action logs
            return AuditLog.objects.filter(user=user)
        
        return AuditLog.objects.none()
    
    @action(detail=False, methods=['get'], url_path='security-events')
    def security_events(self, request):
        """Get security-related events (failed logins, permission denials)"""
        user = request.user
        
        # Only show security events for the current user
        security_actions = ['login', 'logout', 'permission_denied']
        logs = AuditLog.objects.filter(
            user=user,
            action__in=security_actions
        ).order_by('-created_at')[:50]  # Last 50 security events
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
