from django.contrib import admin
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest, SharedEncryptionKey


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_encrypted_id', 'get_encrypted_user', 'get_encrypted_organisation', 'get_encrypted_keycloak_id']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'organisation', 'keycloak_id']
    readonly_fields = ['keycloak_id']
    
    def get_encrypted_id(self, obj):
        """Display encrypted ID"""
        import hashlib
        hashed = hashlib.sha256(str(obj.id).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_id.short_description = 'ID'
    
    def get_encrypted_user(self, obj):
        """Display encrypted user info"""
        import hashlib
        user_info = f"{obj.user.username}_{obj.user.id}"
        hashed = hashlib.sha256(user_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_user.short_description = 'User'
    
    def get_encrypted_organisation(self, obj):
        """Display encrypted organisation"""
        import hashlib
        hashed = hashlib.sha256(obj.organisation.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_organisation.short_description = 'Organisation'
    
    def get_encrypted_keycloak_id(self, obj):
        """Display encrypted keycloak ID"""
        if not obj.keycloak_id:
            return '-'
        import hashlib
        hashed = hashlib.sha256(obj.keycloak_id.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_keycloak_id.short_description = 'Keycloak ID'


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['get_encrypted_id', 'get_encrypted_username', 'get_encrypted_first_name', 'get_encrypted_last_name', 'keycloak_id']
    search_fields = ['user__username', 'keycloak_id']
    filter_horizontal = ['appointed_doctors']
    readonly_fields = ['keycloak_id', 'encrypted_first_name', 'encrypted_last_name', 'encrypted_date_of_birth']
    
    def get_encrypted_id(self, obj):
        """Display encrypted/masked ID"""
        import hashlib
        hashed = hashlib.sha256(str(obj.id).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_id.short_description = 'ID'
    
    def get_encrypted_username(self, obj):
        """Display encrypted/masked username"""
        import hashlib
        hashed = hashlib.sha256(obj.user.username.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_username.short_description = 'Username'
    
    def get_encrypted_first_name(self, obj):
        """Display encrypted first name (truncated)"""
        if obj.encrypted_first_name:
            return obj.encrypted_first_name[:50] + '...'
        return '-'
    get_encrypted_first_name.short_description = 'First Name'
    
    def get_encrypted_last_name(self, obj):
        """Display encrypted last name (truncated)"""
        if obj.encrypted_last_name:
            return obj.encrypted_last_name[:50] + '...'
        return '-'
    get_encrypted_last_name.short_description = 'Last Name'


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = ['get_encrypted_file_id', 'get_encrypted_patient', 'get_encrypted_uploader', 'get_encrypted_filename', 'get_encrypted_created_at']
    list_filter = ['created_at']
    search_fields = ['id', 'patient__user__username', 'uploaded_by__username']
    readonly_fields = ['created_at', 'updated_at', 'encrypted_name', 'encrypted_description', 'encrypted_date']
    
    def get_encrypted_file_id(self, obj):
        """Display encrypted file ID"""
        import hashlib
        hashed = hashlib.sha256(str(obj.id).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_file_id.short_description = 'File ID'
    
    def get_encrypted_patient(self, obj):
        """Display patient info encrypted"""
        if not obj.patient:
            return '-'
        import hashlib
        patient_info = f"{obj.patient.user.username}_{obj.patient.id}"
        hashed = hashlib.sha256(patient_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_patient.short_description = 'Patient'
    
    def get_encrypted_uploader(self, obj):
        """Display uploader info encrypted"""
        if not obj.uploaded_by:
            return '-'
        import hashlib
        hashed = hashlib.sha256(obj.uploaded_by.username.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_uploader.short_description = 'Uploaded By'
    
    def get_encrypted_filename(self, obj):
        """Display encrypted filename"""
        if obj.encrypted_name:
            return obj.encrypted_name[:50] + '...'
        return '-'
    get_encrypted_filename.short_description = 'Filename'
    
    def get_encrypted_created_at(self, obj):
        """Display encrypted creation date"""
        import hashlib
        hashed = hashlib.sha256(str(obj.created_at).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_created_at.short_description = 'Created At'


@admin.register(DoctorPatientRequest)
class DoctorPatientRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_encrypted_doctor', 'get_encrypted_patient', 'get_encrypted_status', 'get_encrypted_created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['doctor__user__username', 'patient__user__username']
    readonly_fields = ['created_at']
    
    def get_encrypted_doctor(self, obj):
        """Display doctor info encrypted"""
        if not obj.doctor:
            return '-'
        import hashlib
        doctor_info = f"{obj.doctor.user.username}_{obj.doctor.id}"
        hashed = hashlib.sha256(doctor_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_doctor.short_description = 'Doctor'
    
    def get_encrypted_patient(self, obj):
        """Display patient info encrypted"""
        if not obj.patient:
            return '-'
        import hashlib
        patient_info = f"{obj.patient.user.username}_{obj.patient.id}"
        hashed = hashlib.sha256(patient_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_patient.short_description = 'Patient'
    
    def get_encrypted_status(self, obj):
        """Display encrypted status"""
        import hashlib
        hashed = hashlib.sha256(obj.status.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_status.short_description = 'Status'
    
    def get_encrypted_created_at(self, obj):
        """Display encrypted creation date"""
        import hashlib
        hashed = hashlib.sha256(str(obj.created_at).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_created_at.short_description = 'Created At'


@admin.register(FileActionRequest)
class FileActionRequestAdmin(admin.ModelAdmin):
    list_display = ['get_encrypted_request_id', 'get_encrypted_doctor', 'get_encrypted_patient', 'get_encrypted_action_type', 'get_encrypted_status', 'get_encrypted_created_at']
    list_filter = ['action_type', 'status', 'created_at']
    search_fields = ['doctor__user__username', 'target_file__id']
    readonly_fields = ['created_at', 'encrypted_file_name', 'encrypted_file_description', 'encrypted_file_date']
    
    def get_encrypted_request_id(self, obj):
        """Display encrypted request ID"""
        import hashlib
        hashed = hashlib.sha256(str(obj.id).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_request_id.short_description = 'Request ID'
    
    def get_encrypted_doctor(self, obj):
        """Display doctor info encrypted"""
        if not obj.doctor:
            return '-'
        import hashlib
        doctor_info = f"{obj.doctor.user.username}_{obj.doctor.id}"
        hashed = hashlib.sha256(doctor_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_doctor.short_description = 'Doctor'
    
    def get_encrypted_patient(self, obj):
        """Display patient info encrypted"""
        if not obj.patient:
            return '-'
        import hashlib
        patient_info = f"{obj.patient.user.username}_{obj.patient.id}"
        hashed = hashlib.sha256(patient_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_patient.short_description = 'Patient'
    
    def get_encrypted_action_type(self, obj):
        """Display encrypted action type"""
        import hashlib
        hashed = hashlib.sha256(obj.action_type.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_action_type.short_description = 'Action Type'
    
    def get_encrypted_status(self, obj):
        """Display encrypted status"""
        import hashlib
        hashed = hashlib.sha256(obj.status.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_status.short_description = 'Status'
    
    def get_encrypted_created_at(self, obj):
        """Display encrypted creation date"""
        import hashlib
        hashed = hashlib.sha256(str(obj.created_at).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_created_at.short_description = 'Created At'


@admin.register(SharedEncryptionKey)
class SharedEncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ['get_encrypted_id', 'get_encrypted_patient', 'get_encrypted_doctor', 'get_encrypted_created_at']
    search_fields = ['patient__user__username', 'doctor__user__username']
    readonly_fields = ['created_at', 'encrypted_key']
    
    def get_encrypted_id(self, obj):
        """Display encrypted ID"""
        import hashlib
        hashed = hashlib.sha256(str(obj.id).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_id.short_description = 'ID'
    
    def get_encrypted_patient(self, obj):
        """Display encrypted patient info"""
        if not obj.patient:
            return '-'
        import hashlib
        patient_info = f"{obj.patient.user.username}_{obj.patient.id}"
        hashed = hashlib.sha256(patient_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_patient.short_description = 'Patient'
    
    def get_encrypted_doctor(self, obj):
        """Display encrypted doctor info"""
        if not obj.doctor:
            return '-'
        import hashlib
        doctor_info = f"{obj.doctor.user.username}_{obj.doctor.id}"
        hashed = hashlib.sha256(doctor_info.encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_doctor.short_description = 'Doctor'
    
    def get_encrypted_created_at(self, obj):
        """Display encrypted creation date"""
        import hashlib
        hashed = hashlib.sha256(str(obj.created_at).encode()).hexdigest()
        return hashed[:50] + '...'
    get_encrypted_created_at.short_description = 'Created At'
