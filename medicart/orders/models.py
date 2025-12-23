from django.db import models

# Create your models here.
from django.conf import settings
from shop.models import Medicine, Stock
from prescriptions.models import Prescription
import uuid



class Order(models.Model):
    STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('processing', 'Processing'),
    ('out_for_delivery', 'Out for delivery'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]


    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20,unique=True,editable=False, null=True, blank=True)

    pharmacy = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    prescription = models.ForeignKey(Prescription, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    payment_method = models.CharField(  
        max_length=20,
        choices=[
            ("cod", "Cash on Delivery"),
            ("card", "Credit/Debit Card"),
            ("upi", "UPI"),
        ], default="cod"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField(blank=True,null=True)
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        # Example: ORD-A9F3C21B
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    pharmacy = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def line_total(self):
        return self.quantity * self.price