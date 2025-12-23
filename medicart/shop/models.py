from django.db import models

# Create your models here.
from django.conf import settings
from geopy.geocoders import Nominatim  #type: ignore
from geopy.exc import GeocoderTimedOut, GeocoderServiceError  #type: ignore

class Category(models.Model):
    name = models.CharField(max_length=100)


    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    pharmacy = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expiry_date = models.DateField(null=True, blank=True)
    prescription_required = models.BooleanField(default=False)
    image = models.ImageField(upload_to='medicine_images/', null=True, blank=True)
    is_active = models.BooleanField(default=True)  # ✅ NEW


    def __str__(self):
        return f"{self.name} ({self.brand})" if self.brand else self.name


class Stock(models.Model):
    medicine = models.ForeignKey(Medicine, related_name='stocks', on_delete=models.CASCADE)
    pharmacy = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='stocks', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    @property
    def price(self):
        return self.medicine.price

    @property
    def expiry_date(self):
        return self.medicine.expiry_date

    class Meta:
        unique_together = ('medicine', 'pharmacy')

    def is_low(self):
        return self.quantity <= self.low_stock_threshold

    def save(self, *args, **kwargs):
        # price is a computed property backed by medicine.price — do not assign to it.
        super().save(*args, **kwargs)

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    medicine = models.ForeignKey("Medicine", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.medicine.price * self.quantity
