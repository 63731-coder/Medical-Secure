import uuid
from django.db import models
from django.contrib.auth.models import User


class Doctor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    keycloak_id = models.CharField(
        max_length=255, 
        unique=True,
        db_index=True,
        help_text="Keycloak user ID (sub claim)"
    )
    organisation = models.CharField(max_length=100)
    
    # Encrypted sensitive data (client-side encrypted with doctor's key)
    encrypted_organisation = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted organisation (AES-256)"
    )
    encrypted_first_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted first name (AES-256)"
    )
    encrypted_last_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted last name (AES-256)"
    )

    def __str__(self):
        return f"Dr. {self.user.last_name} ({self.organisation})"

    class Meta:
        indexes = [
            models.Index(fields=['keycloak_id']),
        ]


class Patient(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    keycloak_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Keycloak user ID (sub claim)"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Encrypted sensitive data (client-side encrypted with patient's key)
    encrypted_date_of_birth = models.TextField(
        blank=True, 
        null=True,
        help_text="Client-side encrypted date of birth (AES-256)"
    )
    encrypted_first_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted first name (AES-256)"
    )
    encrypted_last_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted last name (AES-256)"
    )

    appointed_doctors = models.ManyToManyField(
        Doctor, related_name="patients", blank=True
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['keycloak_id']),
        ]


class SharedEncryptionKey(models.Model):
    """
    Stores patient encryption keys shared with doctors.
    The patient's encryption key is encrypted with the doctor's key before storage.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='shared_keys')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='received_keys')
    encrypted_key = models.TextField(help_text="Patient's encryption key encrypted with doctor's key")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['patient', 'doctor']
        indexes = [
            models.Index(fields=['patient', 'doctor']),
        ]
    
    def __str__(self):
        return f"Key: {self.patient} → Dr. {self.doctor.user.last_name}"


class DoctorPatientRequest(models.Model):
    """
    Request for a doctor-patient relationship.
    Can be initiated by either the patient or the doctor.
    Requires approval from the patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ACTION_CHOICES = [
        ('add', 'Add'),
        ('remove', 'Remove'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patient_requests')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='doctor_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_requests',
                                    help_text="User who initiated this request")
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES, default='add',
                                   help_text="Type of action: add or remove relationship")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Encrypted sensitive metadata (client-side encrypted with patient's key)
    encrypted_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted file name (AES-256)"
    )
    encrypted_description = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted description (AES-256)"
    )
    encrypted_date = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted examination date (AES-256)"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.doctor} - {self.patient} ({self.action_type}/{self.status})"


class MedicalFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_files"
    )
    file = models.FileField(upload_to="medical_records/")
    # Legacy fields - keep for compatibility but store anonymized placeholders
    # Real data is ONLY in encrypted_* fields
    name = models.CharField(max_length=255, default='[ENCRYPTED]', help_text="Anonymized placeholder - real data in encrypted_name")
    description = models.TextField(blank=True, default='', help_text="Anonymized placeholder - real data in encrypted_description")

    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Encrypted sensitive metadata (client-side encrypted with patient's key)
    encrypted_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted file name (AES-256)"
    )
    encrypted_description = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted description (AES-256)"
    )
    encrypted_date = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted examination date (AES-256)"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.patient.user.username}"


class FileActionRequest(models.Model):
    """
    Request for a file action (upload, edit, delete) initiated by a doctor.
    Requires approval from the patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ACTION_CHOICES = [
        ('upload', 'Upload'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]
    
    # Encrypted sensitive metadata (client-side encrypted with patient's key)
    encrypted_file_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted file name (AES-256)"
    )
    encrypted_file_description = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted description (AES-256)"
    )
    encrypted_file_date = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted examination date (AES-256)"
    )
    
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
        return f"{self.action_type} by Dr. {self.doctor.user.username} for {self.patient} ({self.status})"
    
    def execute_action(self):
        """Execute the approved action"""
        if self.status != 'approved':
            raise ValueError("Can only execute approved actions")
        
        if self.action_type == 'upload':
            # Create new medical file with encrypted metadata
            MedicalFile.objects.create(
                patient=self.patient,
                file=self.file_data,
                name=self.file_name,
                description=self.file_description,
                uploaded_by=self.doctor.user,
                encrypted_name=self.encrypted_file_name,
                encrypted_description=self.encrypted_file_description,
                encrypted_date=self.encrypted_file_date
            )
        
        elif self.action_type == 'edit':
            # Update existing file with encrypted metadata
            if self.target_file:
                # Only update file if new file was uploaded
                if self.file_data:
                    self.target_file.file = self.file_data
                self.target_file.name = self.file_name
                self.target_file.description = self.file_description
                self.target_file.encrypted_name = self.encrypted_file_name
                self.target_file.encrypted_description = self.encrypted_file_description
                self.target_file.encrypted_date = self.encrypted_file_date
                self.target_file.save()
        
        elif self.action_type == 'delete':
            # Delete the file
            if self.target_file:
                self.target_file.file.delete()
                self.target_file.delete()
