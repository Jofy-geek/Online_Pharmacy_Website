from django.db import models

# Create your models here.
from django.conf import settings

class Prescription(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    uploaded_file = models.FileField(upload_to='prescriptions/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    used = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_prescriptions')
    notes = models.TextField(blank=True)


    def __str__(self):
        return f"Prescription #{self.id} by {self.patient.username}"