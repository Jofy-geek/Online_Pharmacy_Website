from django.urls import path
from . import views
from deliveries import views as delivery_views


urlpatterns = [
    path('', views.home_view, name='home'),
    path("register/", views.register_view, name="register"),
    path('users/', views.user_list, name='user_list'),
    path("dashboard/profile/", views.profile_view, name="profile"),
    path("dashboard/profile/<int:pk>/",views.profile_view,name="profile") ,
    path("dashboard/profile/update/", views.update_profile_view, name="update_profile"),
    path("dashboard/profile/update/<int:pk>/", views.update_profile_view, name="update_profile"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("toggle-user-status/<int:pk>/", views.toggle_user_status, name="toggle_user_status"),
    path("assign/<int:order_id>/", delivery_views.assign_delivery, name="assign_delivery"),
    path("unassigned-orders/", delivery_views.unassigned_orders, name="unassigned_orders"),
    path("<int:pk>/picked/", delivery_views.mark_picked, name="mark_picked"),
    path("<int:pk>/delivered/", delivery_views.mark_delivered, name="mark_delivered"),
    path("deliveries/<int:delivery_id>/track/", delivery_views.track_route, name="track_route"),
    path("track-order/", delivery_views.track_order_redirect, name="track_order_redirect"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # Password reset
    path("password-reset/", views.check_email_view, name="password_reset"),
    path("password-reset-confirm/", views.reset_password_view, name="password_reset_confirm"),
]
