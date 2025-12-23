from django.urls import path
from . import views

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("<int:pk>/", views.order_detail, name="order_detail"),
    path("create/", views.create_order, name="create_order"),
    path("<int:pk>/update-status/", views.update_order_status, name="update_order_status"),
]
