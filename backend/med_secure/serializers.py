from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest, SharedEncryptionKey
import re
import bleach
# import magic  # Commented out - libmagic issues on Windows


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
    
    # Encrypted fields (client-side encrypted)
    date_of_birth = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'keycloak_id', 'appointed_doctors',
                 'date_of_birth', 'first_name', 'last_name']


class MedicalFileSerializer(serializers.ModelSerializer):
    """Medical file with metadata"""
    uploaded_by = UserSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    
    # Encrypted fields (client-side encrypted)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = MedicalFile
        fields = ['id', 'file', 'name', 'description', 'date', 'created_at', 'uploaded_by', 'patient']
        read_only_fields = ['uploaded_by', 'created_at', 'patient']
    
    def validate_file(self, value):
        """Validate file size and MIME type"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(f"File size cannot exceed 10MB (current: {value.size / 1024 / 1024:.2f}MB)")
        
        value.seek(0)  # Reset file pointer for later use
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Registration for new users (patient or doctor)"""
    password = serializers.CharField(write_only=True, min_length=8)
    user_type = serializers.ChoiceField(choices=['patient', 'doctor'], write_only=True)
    
    # Optional fields for specific user types
    organisation = serializers.CharField(max_length=100, required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 
                 'user_type', 'organisation']

    def validate(self, data):
        """Custom validation based on user type"""
        user_type = data.get('user_type')
        
        if user_type == 'doctor' and not data.get('organisation'):
            raise serializers.ValidationError("Organisation is required for doctors")
            
        return data

    def create(self, validated_data):
        """Create user and associated profile"""
        user_type = validated_data.pop('user_type')
        organisation = validated_data.pop('organisation', None)
        
        # For patients: clear first_name/last_name (stored only in encrypted fields)
        # For doctors: keep names (trusted users)
        if user_type == 'patient':
            validated_data['first_name'] = ''
            validated_data['last_name'] = ''
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile based on type
        if user_type == 'patient':
            Patient.objects.create(user=user)
        elif user_type == 'doctor':
            Doctor.objects.create(user=user, organisation=organisation)
        
        return user


class DoctorPatientRequestSerializer(serializers.ModelSerializer):
    """Serializer for doctor-patient relationship requests"""
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    requested_by_user = UserSerializer(source='requested_by', read_only=True)
    
    class Meta:
        model = DoctorPatientRequest
        fields = ['id', 'doctor', 'patient', 'requested_by_user', 'action_type', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class FileActionRequestSerializer(serializers.ModelSerializer):
    """Serializer for file action requests (upload, edit, delete) by doctors"""
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    target_file_info = serializers.SerializerMethodField()
    
    # Encrypted fields (client-side encrypted)
    file_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    file_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    file_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = FileActionRequest
        fields = ['id', 'patient', 'doctor', 'action_type', 'status', 
                 'file_name', 'file_description', 'file_date', 'target_file', 'target_file_info',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'patient', 'doctor']
    
    def get_target_file_info(self, obj):
        """Get info about the target file for edit/delete actions"""
        if obj.target_file:
            return {
                'id': obj.target_file.id,
                'name': obj.target_file.name,
                'description': obj.target_file.description,
            }
        return None


class SharedEncryptionKeySerializer(serializers.ModelSerializer):
    """Serializer for sharing encryption keys between patients and doctors"""
    class Meta:
        model = SharedEncryptionKey
        fields = ['id', 'patient', 'doctor', 'key', 'created_at']
        read_only_fields = ['created_at']
