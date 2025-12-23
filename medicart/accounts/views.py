from datetime import datetime, time
from typing import OrderedDict
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from deliveries.models import Delivery

from .forms import RegisterForm, LoginForm, CustomPasswordResetForm, CustomSetPasswordForm, ProfileUpdateForm
from django.contrib.auth import get_user_model
from shop.models import Category
from orders.models import Order
from django.utils import timezone
from prescriptions.models import Prescription
from django.db.models import Sum, F
from django.utils.timezone import now
from shop.models import Stock


User = get_user_model()

# ----------------- Views -----------------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Use password1 from the form
            user.set_password(form.cleaned_data["password1"])
            user.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("login")
        else:
            # Collect form errors and display them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def home_view(request):
    return render(request, "home.html")

@login_required
def dashboard_view(request):
    user = request.user

    # recent activities (optional)
    recent_activities = getattr(user, 'recent_activities', [])

    context = {
        "user": user,
        "recent_activities": recent_activities or [],
    }

    # ---------- Patient Dashboard ----------
    if user.is_patient():
        # Active orders: pending or processing
        active_orders = Order.objects.filter(
            patient=user,
            status__in=['pending', 'processing']
        ).count()


        # Recent prescriptions
        recent_prescriptions = Prescription.objects.filter(
            patient=user
        ).count()
    

        # Update context with stats
        context.update({
            "active_orders": active_orders,
            "recent_prescriptions": recent_prescriptions,
        })

        template_name = "patient_dashboard.html"

    # ---------- Superuser/Admin Dashboard ----------
    elif user.is_superuser:
        total_users = User.objects.filter(is_superuser=False).count()
        total_pharmacies = User.objects.filter(role='pharmacist').count()
        total_orders = Order.objects.count()
        total_categories = Category.objects.count()
        system_alerts = 1  # placeholder, implement as needed


        context.update({
            "total_users": total_users,
            "total_pharmacies": total_pharmacies,
            "total_orders": total_orders,
            "system_alerts": system_alerts,
            "total_categories": total_categories,
        })

         
        template_name = "admin_dashboard.html"

    # ---------- Pharmacist Dashboard ----------
    elif user.is_pharmacist():

        # 1. Pending Orders
        pending_orders = Order.objects.filter(pharmacy=request.user,status="pending").count()

        # 2. Pending Prescriptions
        pending_prescriptions = Prescription.objects.filter(verified=False).count()

        # 3. Low Stock Items (adjust threshold as needed)
        low_stock_items = Stock.objects.filter(quantity__lt=10).count()

        # 4. Monthly Sales (sum of completed orders this month)
        today = now().date()
        monthly_sales = (
            Order.objects.filter(
                status="completed",
                created_at__year=today.year,
                created_at__month=today.month,
            ).aggregate(total=Sum("total_amount"))["total"] or 0
        )

        context.update({
            "pending_orders": pending_orders,
            "pending_prescriptions": pending_prescriptions,
            "low_stock_items": low_stock_items,
            "monthly_sales": monthly_sales,
        })

        # Example: you can add pharmacist-specific stats here
        template_name = "pharmacist_dashboard.html"

    # ---------- Delivery Staff Dashboard ----------
    elif user.is_delivery():
        today = timezone.localdate()
        start_of_day = timezone.make_aware(datetime.combine(today, time.min))
        end_of_day = timezone.make_aware(datetime.combine(today, time.max))

        # Latest delivery
        latest_delivery = Delivery.objects.filter(
            assigned_to=user
        ).exclude(status="delivered").order_by("-id").first()

        # Pending deliveries
        pending_deliveries = Delivery.objects.filter(
            assigned_to=user,
            status="pending"
        ).count()

        # Completed deliveries today (use range)
        completed_today_qs = Delivery.objects.filter(
            assigned_to=user,
            status="delivered",
            delivered_at__range=(start_of_day, end_of_day)
        )
        completed_today = completed_today_qs.count()

        # On-time rate
        total_completed = Delivery.objects.filter(
            assigned_to=user,
            status="delivered"
        ).count()

        on_time_deliveries = Delivery.objects.filter(
            assigned_to=user,
            status="delivered",
            delivered_at__lte=F("expected_delivery_time")
        ).count() if total_completed else 0

        on_time_rate = round((on_time_deliveries / total_completed) * 100, 2) if total_completed else 0
        
        
        context = {
            "latest_delivery": latest_delivery,
            "pending_deliveries": pending_deliveries,
            "completed_today": completed_today,
            "deliveries": completed_today_qs,  # Pass actual deliveries to modal
            "on_time_rate": on_time_rate,
        }

        template_name = "delivery_dashboard.html"

    else:
        messages.error(request, "Role not recognized.")
        return redirect("logout")

    return render(request, template_name, context)

def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.filter(is_superuser=False).count()
    total_pharmacists = User.objects.filter(role='pharmacist').count()
    total_orders = Order.objects.count()
    total_categories = Category.objects.count()

    # Example dummy recent activities
    recent_activities = [
        {"title": "New User Registered", "description": "John Doe created an account", "timestamp": timezone.now()},
        {"title": "Order Placed", "description": "Order #123 by Alice", "timestamp": timezone.now()},
    ]

    context = {
        "total_users": total_users,
        "total_pharmacists": total_pharmacists,
        "total_orders": total_orders,
        "total_categories": total_categories,
        "system_alerts": 1,   # change if you want dynamic alerts
        "recent_activities": recent_activities,

    }
    return render(request, "dashboard.html", context)

                                                                                                                                                                                                                                                                                                                        
@login_required
@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all()

    grouped_users = OrderedDict({
        "Pharmacists": users.filter(role="pharmacist"),
        "Delivery Staff": users.filter(role="delivery"),
        "Patients": users.filter(role="patient"),
    })

    return render(request, "user_list.html", {
        "grouped_users": grouped_users,
    })

    
# Only allow superusers (admins)
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
@admin_required
def toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Cannot deactivate another admin!")
    else:
        user.is_active = not user.is_active
        user.save()
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} has been {status}.")
    return redirect("user_list")



def check_email_view(request):
    """
    Check if an email exists in the database.
    If found, redirect to reset password page.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            messages.error(request, "Email is required.")
            return render(request, "password_reset.html", {"form": CustomPasswordResetForm()})

        try:
            user = User.objects.get(email=email)
            # ✅ Store email temporarily in session so we can use it in reset_password_view
            request.session["reset_email"] = email  
            return redirect("password_reset_confirm")  # redirect to reset password page
        except User.DoesNotExist:
            messages.error(request, "Email not found in our records.")
            return render(request, "password_reset.html", {"form": CustomPasswordResetForm(initial={"email": email})})

    form = CustomPasswordResetForm()
    return render(request, "password_reset.html", {"form": form})


# ----------------- Reset Password View -----------------
def reset_password_view(request):
    """
    Reset password for a user if the email exists.
    """
    email = request.session.get("reset_email")

    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect("password_reset")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("password_reset")

    if request.method == "POST":
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()  # handles hashing automatically
            del request.session["reset_email"]  # clear session
            messages.success(request, "Password has been reset successfully.")
            return redirect("login")
    else:
        form = CustomSetPasswordForm(user)

    return render(request, "password_reset_confirm.html", {"form": form})

# ----------------- Profile View -----------------


@login_required
def profile_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    # 🔒 prevent users viewing others
    if request.user != user and not request.user.is_staff:
        return HttpResponseForbidden("Not allowed")

    return render(request, "profile.html", {"user": user})


@login_required
def update_profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()  # This now handles password too!
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "update_profile.html", {
        "form": form,
        "show_password_section": True
    })


