import uuid
from django.db import models
from django.contrib.auth.models import User


def encrypted_file_path(instance, filename):
    """
    Generate a random filename to hide the original filename in the database.
    The real filename is stored encrypted in the 'name' field.
    """
    # Get file extension (even if it's .enc)
    ext = filename.split('.')[-1] if '.' in filename else ''
    # Generate random UUID for the physical file
    random_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    return f"medical_records/{random_name}"


def pending_file_path(instance, filename):
    """
    Generate a random filename for pending files.
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    random_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    return f"pending_files/{random_name}"


class Doctor(models.Model):
    """
    Doctor profile model. Links to Keycloak authentication.
    Doctors can access patient files with patient approval.
    """
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

    def __str__(self):
        return f"{self.id}"

    class Meta:
        indexes = [
            models.Index(fields=['keycloak_id']),
        ]


class Patient(models.Model):
    """
    Patient profile model. All sensitive data is client-side encrypted.
    Can appoint doctors to access their medical files.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    keycloak_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Keycloak user ID (sub claim)"
    )
    
    # Encrypted sensitive data (client-side encrypted with patient's key)
    date_of_birth = models.TextField(
        blank=True, 
        null=True,
        help_text="Client-side encrypted date of birth (AES-256)"
    )
    first_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted first name (AES-256)"
    )
    last_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted last name (AES-256)"
    )

    appointed_doctors = models.ManyToManyField(
        Doctor, related_name="patients", blank=True
    )

    def __str__(self):
        return f"{self.id}"

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
    key = models.TextField(help_text="Patient's encryption key encrypted with doctor's key")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['patient', 'doctor']
        indexes = [
            models.Index(fields=['patient', 'doctor']),
        ]
    
    def __str__(self):
        return f"{self.id}"


class DoctorPatientRequest(models.Model):
    """
    Request for a doctor-patient relationship.
    Can be initiated by either the patient or the doctor.
    Requires approval from the patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patient_requests')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='doctor_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_requests',
                                    help_text="User who initiated this request")
    
    # Encrypted sensitive data (client-side encrypted with patient's key)
    action_type = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted action type: add or remove relationship (AES-256)"
    )
    status = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted status: pending, approved, or rejected (AES-256)"
    )
    
    # Keep timestamps unencrypted for ordering/filtering (not sensitive data)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{str(self.id)[:8]}"


class MedicalFile(models.Model):
    """
    Medical file storage. All metadata is client-side encrypted.
    Only accessible by patient and appointed doctors.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_files"
    )
    file = models.FileField(upload_to=encrypted_file_path)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )

    # Keep timestamps unencrypted for ordering/filtering (not sensitive data)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Encrypted sensitive metadata (client-side encrypted with patient's key)
    name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted file name (AES-256)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted description (AES-256)"
    )
    date = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted examination date (AES-256)"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{str(self.id)[:8]}"


class FileActionRequest(models.Model):
    """
    Request for a file action (upload, edit, delete) initiated by a doctor.
    Requires approval from the patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='file_action_requests')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='file_action_requests')
    
    # Encrypted sensitive data (client-side encrypted with patient's key)
    action_type = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted action type: upload, edit, or delete (AES-256)"
    )
    status = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted status: pending, approved, or rejected (AES-256)"
    )
    file_name = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted file name (AES-256)"
    )
    file_description = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted description (AES-256)"
    )
    file_date = models.TextField(
        blank=True,
        null=True,
        help_text="Client-side encrypted examination date (AES-256)"
    )
    
    # For upload and edit actions
    file_data = models.FileField(upload_to=pending_file_path, null=True, blank=True,
                                 help_text="File data for upload/edit actions")
    
    # For edit and delete actions - reference to existing file
    target_file = models.ForeignKey(MedicalFile, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='pending_actions',
                                   help_text="The file being edited or deleted")
    
    # Keep timestamps unencrypted for ordering/filtering (not sensitive data)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{str(self.id)[:8]}"
    
    def execute_action(self):
        """Execute the approved action
        Note: action_type is stored in plain text ('upload', 'edit', 'delete')
        so we can use it directly to determine the action.
        """
        # Use action_type directly since it's stored in plain text
        if self.action_type == 'upload':
            # Upload: create new medical file
            MedicalFile.objects.create(
                patient=self.patient,
                file=self.file_data,
                uploaded_by=self.doctor.user,
                name=self.file_name,
                description=self.file_description,
                date=self.file_date
            )
        
        elif self.action_type == 'edit':
            # Edit: update existing file
            if self.target_file:
                # Only update file if new file was uploaded
                if self.file_data:
                    self.target_file.file = self.file_data
                if self.file_name:
                    self.target_file.name = self.file_name
                if self.file_description:
                    self.target_file.description = self.file_description
                if self.file_date:
                    self.target_file.date = self.file_date
                self.target_file.save()
        
        elif self.action_type == 'delete':
            # Delete: remove the file
            if self.target_file:
                self.target_file.file.delete()
                self.target_file.delete()
