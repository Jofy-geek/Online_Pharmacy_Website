from django.db import models

# Create your models here.
from django.conf import settings
from orders.models import Order
import random
import string
from django.contrib.auth import get_user_model
User = get_user_model()


class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_deliveries')
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='assigned')
    tracking_url = models.URLField(blank=True)
    distance = models.FloatField(default=0, help_text="Distance traveled in km")
    expected_delivery_time = models.DateTimeField(null=True, blank=True, help_text="Planned delivery time")
    verification_code = models.CharField(max_length=6, blank=True, null=True)  # ✅ NEW FIELD

    def generate_verification_code(self):
        """Generate a random 6-digit code"""
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.save()


    def __str__(self):
        return f"Delivery for order {self.order.id}"
