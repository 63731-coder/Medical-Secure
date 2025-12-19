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

    appointed_doctors = models.ManyToManyField(
        Doctor, related_name="patients", blank=True
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['keycloak_id']),
        ]


class MedicalFile(models.Model):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_files"
    )
    file = models.FileField(upload_to="medical_records/")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.patient.user.username}"
