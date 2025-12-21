from django.contrib import admin
from .models import Doctor, Patient, MedicalFile, DoctorPatientRequest, FileActionRequest


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'organisation']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'organisation']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date_of_birth']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    filter_horizontal = ['appointed_doctors']


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'patient', 'uploaded_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'patient__user__username']


@admin.register(DoctorPatientRequest)
class DoctorPatientRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'patient', 'requested_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['doctor__user__username', 'patient__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FileActionRequest)
class FileActionRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'action_type', 'doctor', 'patient', 'status', 'created_at']
    list_filter = ['action_type', 'status', 'created_at']
    search_fields = ['doctor__user__username', 'patient__user__username', 'file_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'pending':
            return self.readonly_fields + ['status']
        return self.readonly_fields
