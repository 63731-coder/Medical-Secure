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
    
    # Encrypted fields (client-side encrypted)
    encrypted_organisation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'organisation', 'encrypted_organisation', 
                 'encrypted_first_name', 'encrypted_last_name']


class PatientSerializer(serializers.ModelSerializer):
    """Patient profile with user info and appointed doctors"""
    user = UserSerializer(read_only=True)
    appointed_doctors = DoctorSerializer(many=True, read_only=True)
    
    # Encrypted fields (client-side encrypted)
    encrypted_date_of_birth = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'keycloak_id', 'appointed_doctors',
                 'encrypted_date_of_birth', 'encrypted_first_name', 'encrypted_last_name']


class MedicalFileSerializer(serializers.ModelSerializer):
    """Medical file with metadata"""
    uploaded_by = UserSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    
    # Encrypted fields (client-side encrypted)
    encrypted_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = MedicalFile
        fields = ['id', 'file', 'name', 'description', 'created_at', 'uploaded_by', 'patient',
                 'encrypted_name', 'encrypted_description', 'encrypted_date']
        read_only_fields = ['uploaded_by', 'created_at', 'patient']
    
    def validate_name(self, value):
        """Prevent path traversal attacks in filenames"""
        # Check for path traversal patterns
        if '..' in value:
            raise serializers.ValidationError("Filename cannot contain '..'")
        
        # Check for directory separators
        if '/' in value or '\\' in value:
            raise serializers.ValidationError("Filename cannot contain path separators")
        
        # Check for dangerous characters (Windows/Linux)
        dangerous_chars = r'[<>:"|?*\x00-\x1f]'
        if re.search(dangerous_chars, value):
            raise serializers.ValidationError("Filename contains invalid characters")
        
        # Check for reserved Windows names
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if value.upper().split('.')[0] in reserved_names:
            raise serializers.ValidationError("Filename uses a reserved system name")
        
        return value
    
    def validate_description(self, value):
        """Sanitize HTML/JavaScript to prevent XSS attacks"""
        # Whitelist approach: strip all HTML tags
        sanitized = bleach.clean(value, tags=[], strip=True)
        return sanitized
    
    def validate_file(self, value):
        """Validate file size and MIME type"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(f"File size cannot exceed 10MB (current: {value.size / 1024 / 1024:.2f}MB)")
        
        # Check MIME type using python-magic (reads file content)
        # NOTE: Disabled due to libmagic Windows compatibility issues
        # value.seek(0)  # Reset file pointer
        # file_content = value.read(1024)  # Read first 1KB
        # value.seek(0)  # Reset again for later use
        
        # mime = magic.from_buffer(file_content, mime=True)
        
        # For now, skip MIME validation (accept all files)
        # In production, could use file extension validation instead
        value.seek(0)  # Reset file pointer for later use
        
        # Whitelist of allowed MIME types (currently not enforced)
        # allowed_mimes = [
        #     'application/pdf',           # PDF documents
        #     'image/jpeg',                # JPEG images
        #     'image/png',                 # PNG images
        #     'image/gif',                 # GIF images
        #     'application/octet-stream',  # Encrypted files
        #     'text/plain',                # Text files
        # ]
        
        # MIME validation disabled (Windows compatibility)
        # if mime not in allowed_mimes:
        #     raise serializers.ValidationError(
        #         f"File type '{mime}' not allowed. Allowed types: PDF, JPEG, PNG, GIF, TXT, encrypted files"
        #     )
        
        return value


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
    encrypted_file_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_file_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    encrypted_file_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = FileActionRequest
        fields = ['id', 'patient', 'doctor', 'action_type', 'status', 
                 'file_name', 'file_description', 'target_file', 'target_file_info',
                 'encrypted_file_name', 'encrypted_file_description', 'encrypted_file_date',
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
        fields = ['id', 'patient', 'doctor', 'encrypted_key', 'created_at']
        read_only_fields = ['created_at']
