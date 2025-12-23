from django.db import models
from django.contrib.auth.models import AbstractUser
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


class User(AbstractUser):
    ROLE_CHOICES = (
    ("patient", "Public User"),
    ("pharmacist", "Pharmacist"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="admin")
    pharmacy_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Ensure staff/superuser are admin and approved
        if self.is_superuser or self.is_staff:
            self.role = "admin"
            self.approved = True
        if not self.pk:  # ← object is being created for the first time
            if self.role in ("patient", "delivery"):
                self.approved = True
            elif self.role == "pharmacist":
                self.approved = False

        # Auto-geocode only if address provided and coords are missing
        if self.address and (self.latitude is None or self.longitude is None):
            try:
                geolocator = Nominatim(user_agent="medicart_app")
                location = geolocator.geocode(self.address, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
            except (GeocoderTimedOut, GeocoderServiceError):
                # keep existing behavior: don't block save on geocode failure
                print("⚠️ Geocoding service error — could not fetch coordinates")

        super().save(*args, **kwargs)

    def is_patient(self):
        return self.role == "patient"

    def is_pharmacist(self):
        return self.role == "pharmacist"

    def is_delivery(self):
        return self.role == "delivery"
