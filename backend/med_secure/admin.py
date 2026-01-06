from django.contrib import admin
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest, SharedEncryptionKey


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # Only show ID and public professional info (organisation)
    # Hide: user, keycloak_id (identification data)
    list_display = ['id', 'organisation']
    search_fields = ['id', 'organisation']
    readonly_fields = ['id']
    fields = ['id', 'organisation']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # Only show ID and encrypted fields (Base64 blobs)
    # Hide: user, keycloak_id (identification data)
    list_display = ['id', 'first_name', 'last_name', 'date_of_birth']
    search_fields = ['id']
    readonly_fields = ['id', 'first_name', 'last_name', 'date_of_birth']
    fields = ['id', 'first_name', 'last_name', 'date_of_birth']
    # Hide appointed_doctors relation to avoid exposing IDs


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    # Only show ID, encrypted fields (Base64), timestamps
    # Hide: patient, uploaded_by (identification data)
    list_display = ['id', 'name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'name', 'description', 'date', 'file']
    fields = ['id', 'file', 'name', 'description', 'date', 'created_at', 'updated_at']


@admin.register(DoctorPatientRequest)
class DoctorPatientRequestAdmin(admin.ModelAdmin):
    # Only show ID and timestamps - hide action_type/status (not encrypted, sensitive)
    list_display = ['id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fields = ['id', 'created_at', 'updated_at']


@admin.register(FileActionRequest)
class FileActionRequestAdmin(admin.ModelAdmin):
    # Only show ID, encrypted fields, timestamps - hide action_type/status (not encrypted, sensitive)
    list_display = ['id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'file_name', 'file_description', 'file_date', 'file_data']
    fields = ['id', 'file_name', 'file_description', 'file_date', 'file_data', 'created_at', 'updated_at']


@admin.register(SharedEncryptionKey)
class SharedEncryptionKeyAdmin(admin.ModelAdmin):
    # Only show ID, encrypted key (Base64), timestamps
    # Hide: patient, doctor (identification data)
    list_display = ['id', 'key', 'created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'key']
    fields = ['id', 'key', 'created_at']
