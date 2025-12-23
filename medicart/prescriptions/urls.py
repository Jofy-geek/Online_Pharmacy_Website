from django.urls import path
from . import views

urlpatterns = [
    path("", views.prescription_list, name="prescription_list"),
    path("<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("upload/", views.upload_prescription, name="upload_prescription"),
    path("<int:pk>/verify/", views.verify_prescription, name="verify_prescription"),
]
