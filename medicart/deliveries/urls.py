from django.urls import path
from . import views

urlpatterns = [
    path("", views.delivery_list, name="delivery_list"),
    path("<int:pk>/", views.delivery_detail, name="delivery_detail"),
    path("assign/<int:order_id>/", views.assign_delivery, name="assign_delivery"),
    path("unassigned-orders/", views.unassigned_orders, name="unassigned_orders"),
    path("<int:pk>/picked/", views.mark_picked, name="mark_picked"),
    path("<int:pk>/delivered/", views.mark_delivered, name="mark_delivered"),
    path("deliveries/<int:delivery_id>/track/", views.track_route, name="track_route"),
    path("track-order/", views.track_order_redirect, name="track_order_redirect"),
    path("today/", views.today_deliveries, name="today_deliveries"),
    path("verify/<int:delivery_id>/", views.verify_delivery_code, name="verify_delivery_code"),
    path("delivery/register/", views.register_delivery_person, name="register_delivery_person"),
]