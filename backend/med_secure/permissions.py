from rest_framework import permissions
from .models import Doctor, Patient


class IsPatientOwner(permissions.BasePermission):
    """
    Permission to check if user is the patient owner of a medical file
    """
    def has_object_permission(self, request, view, obj):
        # Check if user has patient profile
        if not hasattr(request.user, 'patient_profile'):
            return False
        
        # Check ownership based on object type
        if hasattr(obj, 'patient'):
            return obj.patient == request.user.patient_profile
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAppointedDoctor(permissions.BasePermission):
    """
    Permission to check if user is an appointed doctor for a patient
    """
    def has_object_permission(self, request, view, obj):
        # Check if user has doctor profile
        if not hasattr(request.user, 'doctor_profile'):
            return False
        
        # Get patient from object
        patient = None
        if hasattr(obj, 'patient'):
            patient = obj.patient
        elif hasattr(obj, 'target_patient'):
            patient = obj.target_patient
        
        if not patient:
            return False
        
        # Check if doctor is appointed to this patient
        return patient.appointed_doctors.filter(id=request.user.doctor_profile.id).exists()


class IsDoctor(permissions.BasePermission):
    """
    Permission to check if user is a doctor
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'doctor_profile')


class IsPatient(permissions.BasePermission):
    """
    Permission to check if user is a patient
    """
    def has_permission(self, request, view):
        return hasattr(request.user, 'patient_profile')


class CanViewMedicalFile(permissions.BasePermission):
    """
    Permission to check if user can view a medical file
    Rules:
    - Patient owner can always view
    - Appointed doctor can view if file is approved
    - Uploader can view their own upload
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Patient owner can always view
        if hasattr(user, 'patient_profile') and obj.patient == user.patient_profile:
            return True
        
        # Uploader can view their own upload
        if obj.uploaded_by == user:
            return True
        
        # Appointed doctor can view if approved
        if hasattr(user, 'doctor_profile'):
            is_appointed = obj.patient.appointed_doctors.filter(id=user.doctor_profile.id).exists()
            return is_appointed and obj.approved
        
        return False


class CanModifyMedicalFile(permissions.BasePermission):
    """
    Permission to check if user can modify/delete a medical file
    Rules:
    - Only patient owner can directly modify/delete
    - Doctors must create FileActionRequest
    """
    def has_object_permission(self, request, view, obj):
        # Only patient owner can modify/delete directly
        if hasattr(request.user, 'patient_profile'):
            return obj.patient == request.user.patient_profile
        return False


class CanApproveRequest(permissions.BasePermission):
    """
    Permission to check if user can approve/reject a request
    Rules:
    - Only the target patient can approve/reject
    """
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'patient_profile'):
            return False
        
        # For FileActionRequest
        if hasattr(obj, 'patient'):
            patient = obj.patient
            return patient == request.user.patient_profile
        
        # For AppointmentRequest
        if hasattr(obj, 'patient'):
            return obj.patient == request.user.patient_profile
        
        return False
