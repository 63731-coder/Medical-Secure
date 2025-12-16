from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):
    """
    Doctor profile linked to Django User.
    A doctor belongs to a medical organization.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    organisation = models.CharField(max_length=100, help_text="Hospital or clinic")

    def __str__(self):
        return f"Dr. {self.user.last_name} ({self.organisation})"


class Patient(models.Model):
    """
    Patient profile linked to Django User.
    A patient can have multiple appointed doctors (many-to-many).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    # Many-to-many relation: a patient can have multiple doctors
    appointed_doctors = models.ManyToManyField(Doctor, related_name='patients', blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class MedicalFile(models.Model):
    """
    Medical file belonging to a patient.
    Can be uploaded by the patient or by an appointed doctor.
    For now: plain storage (will be encrypted later).
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_files')
    # File storage (temporarily in plain text)
    file = models.FileField(upload_to='medical_records/')
    name = models.CharField(max_length=255, help_text="Medical file name")
    description = models.TextField(blank=True, help_text="Optional description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Traceability: who uploaded this file?
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  help_text="Patient or doctor who uploaded")
    
    # Approval flag: patient must approve files uploaded/changed by doctors
    approved = models.BooleanField(default=True, help_text="Whether the patient approved this file/action")

    class Meta:
        ordering = ['-created_at']  # Most recent first

    def __str__(self):
        return f"{self.name} - {self.patient.user.last_name}"


class AppointmentRequest(models.Model):
    """
    Doctor requests to be appointed to a patient. Patient must approve.
    """
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointment_requests')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointment_requests')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AppointmentRequest: Dr {self.doctor.user.last_name} -> {self.patient.user.get_full_name()} ({self.status})"


class FileActionRequest(models.Model):
    """
    Represents a doctor-initiated action on a MedicalFile that requires patient approval.
    action_type: upload / modify / delete
    """
    ACTION_UPLOAD = 'upload'
    ACTION_MODIFY = 'modify'
    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_UPLOAD, 'Upload'),
        (ACTION_MODIFY, 'Modify'),
        (ACTION_DELETE, 'Delete'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    # For uploads: `medical_file` may be null and the uploaded file is stored on this request until approval.
    medical_file = models.ForeignKey(MedicalFile, on_delete=models.CASCADE, related_name='action_requests', null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # Target patient for new file uploads
    target_patient = models.ForeignKey(Patient, on_delete=models.CASCADE, 
                                      related_name='file_action_requests', null=True, blank=True,
                                      help_text="Target patient for new file uploads")
    # Temporary storage for pending uploads/modifications
    file = models.FileField(upload_to='medical_records/pending/', null=True, blank=True)
    name = models.CharField(max_length=255, help_text="Pending file name", null=True, blank=True)
    description = models.TextField(blank=True, help_text="Pending description")
    action_type = models.CharField(max_length=16, choices=ACTION_CHOICES)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"FileActionRequest({self.action_type}) on {self.medical_file_id} by {self.requested_by_id} - {self.status}"

    @property
    def patient(self):
        """Get the patient related to this request"""
        if self.medical_file:
            return self.medical_file.patient
        # For new uploads, use target_patient field
        return self.target_patient


class Notification(models.Model):
    """
    Notification system for medical file actions requiring approval
    """
    NOTIFICATION_TYPES = [
        ('file_action_request', 'File Action Request'),
        ('appointment_request', 'Appointment Request'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Link to relevant objects
    file_action_request = models.ForeignKey(FileActionRequest, on_delete=models.CASCADE, null=True, blank=True)
    appointment_request = models.ForeignKey(AppointmentRequest, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification: {self.title} to {self.recipient.username}"


class AuditLog(models.Model):
    """
    Audit trail for all medical file actions and security events
    """
    ACTION_TYPES = [
        ('view_file', 'View File'),
        ('download_file', 'Download File'),
        ('upload_file', 'Upload File'),
        ('modify_file', 'Modify File'),
        ('delete_file', 'Delete File'),
        ('approve_request', 'Approve Request'),
        ('reject_request', 'Reject Request'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_denied', 'Permission Denied'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Context data
    medical_file = models.ForeignKey(MedicalFile, on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)  # Additional metadata
    
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['patient', '-created_at']),
        ]

    def __str__(self):
        return f"AuditLog: {self.user} - {self.action} at {self.created_at}"
