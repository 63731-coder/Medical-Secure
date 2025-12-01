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

    class Meta:
        ordering = ['-created_at']  # Most recent first

    def __str__(self):
        return f"{self.name} - {self.patient.user.last_name}"
