from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile, AppointmentRequest, FileActionRequest, Notification, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Basic user info for API responses"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DoctorSerializer(serializers.ModelSerializer):
    """Doctor profile with user info"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'organisation']


class PatientSerializer(serializers.ModelSerializer):
    """Patient profile with user info and appointed doctors"""
    user = UserSerializer(read_only=True)
    appointed_doctors = DoctorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'appointed_doctors']


class MedicalFileSerializer(serializers.ModelSerializer):
    """Medical file with metadata. Sensitive fields (file URL, name, created_at)
    are only exposed to allowed users (patient owner, uploader, or appointed doctor
    after patient approval).
    """
    uploaded_by = UserSerializer(read_only=True)
    file = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = MedicalFile
        fields = ['id', 'file', 'name', 'description', 'created_at', 'uploaded_by', 'approved']
        read_only_fields = ['uploaded_by', 'created_at', 'approved']

    def _user_is_patient_owner(self, user, medical_file):
        return hasattr(user, 'patient_profile') and medical_file.patient == user.patient_profile

    def _user_is_uploader(self, user, medical_file):
        return medical_file.uploaded_by == user

    def _user_is_appointed_doctor(self, user, medical_file):
        return hasattr(user, 'doctor_profile') and medical_file.patient.appointed_doctors.filter(id=user.doctor_profile.id).exists()

    def _can_view_sensitive(self, user, medical_file):
        # Patient owner always can
        if self._user_is_patient_owner(user, medical_file):
            return True
        # Uploader may view their own upload
        if self._user_is_uploader(user, medical_file):
            return True
        # Appointed doctor can view only if file approved
        if self._user_is_appointed_doctor(user, medical_file) and medical_file.approved:
            return True
        return False

    def get_file(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and self._can_view_sensitive(user, obj):
            # Return download endpoint rather than direct storage URL
            return request.build_absolute_uri(f"/api/files/{obj.id}/download/")
        return None

    def get_name(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and self._can_view_sensitive(user, obj):
            return obj.name
        return None

    def get_created_at(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and self._can_view_sensitive(user, obj):
            return obj.created_at
        return None


class AppointmentRequestSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = AppointmentRequest
        fields = ['id', 'doctor', 'patient', 'status', 'created_at']


class FileActionRequestSerializer(serializers.ModelSerializer):
    requested_by = UserSerializer(read_only=True)
    medical_file = MedicalFileSerializer(read_only=True)
    target_patient = PatientSerializer(read_only=True)

    class Meta:
        model = FileActionRequest
        fields = ['id', 'medical_file', 'target_patient', 'action_type', 'status', 'requested_by', 
                 'note', 'file', 'name', 'description', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Registration for new users (patient or doctor)"""
    password = serializers.CharField(write_only=True, min_length=8)
    user_type = serializers.ChoiceField(choices=['patient', 'doctor'], write_only=True)
    
    # Optional fields for specific user types
    date_of_birth = serializers.DateField(required=False, write_only=True)
    organisation = serializers.CharField(max_length=100, required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 
                 'user_type', 'date_of_birth', 'organisation']

    def validate(self, data):
        """Custom validation based on user type"""
        user_type = data.get('user_type')
        
        if user_type == 'patient' and not data.get('date_of_birth'):
            raise serializers.ValidationError("Date of birth is required for patients")
        
        if user_type == 'doctor' and not data.get('organisation'):
            raise serializers.ValidationError("Organisation is required for doctors")
            
        return data

    def create(self, validated_data):
        """Create user and associated profile"""
        user_type = validated_data.pop('user_type')
        date_of_birth = validated_data.pop('date_of_birth', None)
        organisation = validated_data.pop('organisation', None)
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile based on type
        if user_type == 'patient':
            Patient.objects.create(user=user, date_of_birth=date_of_birth)
        elif user_type == 'doctor':
            Doctor.objects.create(user=user, organisation=organisation)
        
        return user


class NotificationSerializer(serializers.ModelSerializer):
    """Notification with related objects"""
    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    file_action_request = FileActionRequestSerializer(read_only=True)
    appointment_request = AppointmentRequestSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'sender', 'notification_type', 'title', 'message',
                 'file_action_request', 'appointment_request', 'is_read', 'created_at', 'read_at']
        read_only_fields = ['created_at', 'read_at']

    def create(self, validated_data):
        """Create notification with automatic message formatting"""
        notification = super().create(validated_data)
        # Format message based on type
        if notification.file_action_request:
            action = notification.file_action_request.action_type
            file_name = notification.file_action_request.name or notification.file_action_request.medical_file.name
            notification.message = f"Doctor {notification.sender.get_full_name()} wants to {action} file: {file_name}"
            notification.save()
        return notification


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log entry for security tracking"""
    user = UserSerializer(read_only=True)
    medical_file = serializers.PrimaryKeyRelatedField(read_only=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'ip_address', 'user_agent', 'medical_file', 
                 'patient', 'details', 'success', 'error_message', 'created_at']
        read_only_fields = ['created_at']