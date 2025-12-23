from django import forms
from .models import *
from geopy.geocoders import Nominatim  #type: ignore

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "brand", "category", "description", "sku", "price","expiry_date",'image',"prescription_required"]

        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'placeholder': 'Enter Stock Keeping Unit'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'image': 'Medicine Image',
        }

  

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ["medicine", "quantity", "low_stock_threshold"]
    
