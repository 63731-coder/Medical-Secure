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


class DoctorPatientRequest(models.Model):
    """
    Request for a doctor-patient relationship.
    Can be initiated by either the patient or the doctor.
    Requires approval from the patient.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patient_requests')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='doctor_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_requests',
                                    help_text="User who initiated this request")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['doctor', 'patient']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.doctor} - {self.patient} ({self.status})"


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

    class Meta:
        ordering = ['-created_at']  # Most recent first

    def __str__(self):
        return f"{self.name} - {self.patient.user.last_name}"


class FileActionRequest(models.Model):
    """
    Request for a file action (upload, edit, delete) initiated by a doctor.
    Requires approval from the patient.
    """
    ACTION_CHOICES = [
        ('upload', 'Upload'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='file_action_requests')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='file_action_requests')
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # For upload and edit actions
    file_data = models.FileField(upload_to='pending_files/', null=True, blank=True,
                                 help_text="File data for upload/edit actions")
    file_name = models.CharField(max_length=255, blank=True, help_text="Name for the file")
    file_description = models.TextField(blank=True, help_text="Description for the file")
    
    # For edit and delete actions - reference to existing file
    target_file = models.ForeignKey(MedicalFile, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='pending_actions',
                                   help_text="The file being edited or deleted")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_type} by Dr. {self.doctor.user.last_name} for {self.patient} ({self.status})"
    
    def execute_action(self):
        """Execute the approved action"""
        if self.status != 'approved':
            raise ValueError("Can only execute approved actions")
        
        if self.action_type == 'upload':
            # Create new medical file
            MedicalFile.objects.create(
                patient=self.patient,
                file=self.file_data,
                name=self.file_name,
                description=self.file_description,
                uploaded_by=self.doctor.user
            )
        
        elif self.action_type == 'edit':
            # Update existing file
            if self.target_file:
                self.target_file.file = self.file_data
                self.target_file.name = self.file_name
                self.target_file.description = self.file_description
                self.target_file.save()
        
        elif self.action_type == 'delete':
            # Delete the file
            if self.target_file:
                self.target_file.file.delete()
                self.target_file.delete()
