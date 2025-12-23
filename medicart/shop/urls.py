from django.urls import path
from . import views

urlpatterns = [
    # Pharmacy
    path("pharmacies/", views.pharmacy_list, name="pharmacy_list"),
    path("pharmacies/<int:pk>/", views.pharmacy_detail, name="pharmacy_detail"),
    path("pharmacies/<int:id>/approve/", views.pharmacy_approve_toggle, name="pharmacy_approve_toggle"),
    path("pharmacies/<int:pk>/delete/", views.pharmacy_delete, name="pharmacy_delete"),

    # Categories
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/update/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"), 

    # Medicines
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/create/", views.medicine_create, name="medicine_create"),
    path("medicines/<int:pk>/update/", views.medicine_update, name="medicine_update"),
    path("medicines/<int:pk>/", views.medicine_detail, name="medicine_detail"),
    path("medicines/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("medicine/toggle/<int:med_id>/", views.toggle_medicine_status, name="medicine_toggle"),



    # Stocks
    path("stocks/", views.stock_list, name="stock_list"),
    path("stocks/create/", views.stock_create, name="stock_create"),
    path("stocks/<int:pk>/", views.stock_detail, name="stock_detail"),
    path("stocks/<int:pk>/update/", views.stock_update, name="stock_update"),
    path("stocks/<int:pk>/delete/", views.stock_delete, name="stock_delete"),


    # Cart URLs
    path("cart/add-multiple/", views.add_multiple_to_cart, name="add_multiple_to_cart"),
    path("cart/remove-item/<int:item_id>/", views.remove_cart_item, name="remove_cart_item"),
    path("cart/", views.view_cart, name="view_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("cart/update/", views.update_cart, name="update_cart"),
]
