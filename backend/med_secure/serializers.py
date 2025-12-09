from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, Patient, MedicalFile


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
    """Medical file with metadata"""
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = MedicalFile
        fields = ['id', 'file', 'name', 'description', 'created_at', 'uploaded_by']
        read_only_fields = ['uploaded_by', 'created_at']


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