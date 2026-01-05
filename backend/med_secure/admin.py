from django.contrib import admin
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest, SharedEncryptionKey


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'organisation', 'keycloak_id']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'organisation', 'keycloak_id']
    readonly_fields = ['keycloak_id']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'keycloak_id']
    search_fields = ['user__username', 'keycloak_id']
    filter_horizontal = ['appointed_doctors']
    readonly_fields = ['keycloak_id', 'first_name', 'last_name', 'date_of_birth']


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['id', 'patient__user__username', 'uploaded_by__username']
    readonly_fields = ['created_at', 'updated_at', 'name', 'description', 'date']


@admin.register(DoctorPatientRequest)
class DoctorPatientRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'patient', 'created_at']
    list_filter = ['created_at']
    search_fields = ['doctor__user__username', 'patient__user__username']
    readonly_fields = ['created_at', 'action_type', 'status']


@admin.register(FileActionRequest)
class FileActionRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'patient', 'created_at']
    list_filter = ['created_at']
    search_fields = ['doctor__user__username', 'patient__user__username']
    readonly_fields = ['created_at', 'action_type', 'status', 'file_name', 'file_description', 'file_date']


@admin.register(SharedEncryptionKey)
class SharedEncryptionKeyAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'created_at']
    search_fields = ['patient__user__username', 'doctor__user__username']
    readonly_fields = ['created_at', 'key']
