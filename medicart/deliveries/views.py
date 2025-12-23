from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages

from .models import Delivery
from orders.models import Order
from accounts.models import User 
from django.utils.timezone import now
from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim  #type: ignore

from django.core.mail import send_mail
from django.conf import settings
import traceback


from django.contrib.auth.hashers import make_password


@login_required
def delivery_list(request):
    user = request.user

    # ----------------------------
    # PHARMACIST VIEW
    # ----------------------------
    if user.role == "pharmacist":

        # Deliveries for THIS pharmacist's orders
        deliveries = Delivery.objects.filter(
            order__pharmacy=user
        )

        # 🔁 Infer delivery staff from assignments (RATION PROJECT STYLE)
        delivery_staff = (
            User.objects.filter(
                assigned_deliveries__order__pharmacy=user
            )
            .distinct()
        )

    # ----------------------------
    # DELIVERY USER VIEW
    # ----------------------------
    elif user.is_delivery():
        deliveries = Delivery.objects.filter(assigned_to=user)
        delivery_staff = None

    # ----------------------------
    # ADMIN VIEW
    # ----------------------------
    elif user.is_staff or user.is_superuser:
        deliveries = Delivery.objects.all()
        delivery_staff = User.objects.filter(
            assigned_deliveries__isnull=False
        ).distinct()

    else:
        deliveries = Delivery.objects.none()
        delivery_staff = None

    return render(
        request,
        "delivery_list.html",
        {
            "deliveries": deliveries,
            "delivery_staff": delivery_staff,
        }
    )  
    


@login_required
def delivery_detail(request, pk):
    """Delivery details page."""

    delivery = get_object_or_404(
        Delivery.objects.select_related(
            "order",
            "order__pharmacy",
            "assigned_to",
        ),
        pk=pk
    )

    order = delivery.order

    # 🔹 patient who placed the order
    customer = order.patient 

    # 🔹 order items (products in order)
    items = order.items.select_related("medicine")

    # 🔹 pickup shop / pharmacist
    pickup_shop = order.pharmacy

    return render(
        request,
        "delivery_detail.html",
        {
            "delivery": delivery,
            "order": order,
            "customer": customer,
            "items": items,
            "pickup_shop": pickup_shop,
        }
    )


@login_required
def assign_delivery(request, order_id):
    """Assign a delivery person to a pharmacy order (ration-style logic)."""

    # -----------------------------
    # Permission check
    # -----------------------------
    if not (request.user.is_superuser or request.user.role == "pharmacist"):
        messages.error(request, "You don’t have permission to assign deliveries.")
        return redirect("delivery_list")

    # -----------------------------
    # Fetch order
    # -----------------------------
    order = get_object_or_404(Order, id=order_id)

    # Pharmacist can assign ONLY their own orders
    if request.user.role == "pharmacist" and order.pharmacy != request.user:
        return HttpResponseForbidden("Access denied")

    # -----------------------------
    # DO NOT create Delivery on GET
    # -----------------------------
    delivery = Delivery.objects.filter(order=order).first()

    # -----------------------------
    # RATION-STYLE: infer delivery people
    # -----------------------------
    delivery_people = (
        User.objects.filter(
            assigned_deliveries__order__pharmacy=request.user
        )
        .distinct()
    )

    # -----------------------------
    # POST → Assign delivery
    # -----------------------------
    if request.method == "POST":
        assigned_id = request.POST.get("assigned_to")

        if not assigned_id:
            messages.error(request, "Please select a delivery person before submitting.")
            return redirect("assign_delivery", order_id=order.id)

        # ✅ FIX: get ONLY by PK
        person = get_object_or_404(User, id=assigned_id)

        # ✅ SECURITY CHECK (ration-style ownership validation)
        if not delivery_people.filter(id=person.id).exists():
            return HttpResponseForbidden("Invalid delivery person selected.")

        # NOW create Delivery object if it doesn't exist
        if not delivery:
            delivery = Delivery.objects.create(order=order)

        delivery.assigned_to = person
        delivery.status = "assigned"
        delivery.save()

        return redirect("delivery_list")

    # -----------------------------
    # GET → Render page
    # -----------------------------
    return render(
        request,
        "assign_delivery.html",
        {
            "order": order,
            "delivery_people": delivery_people,
            "assigned_person": delivery.assigned_to.id if delivery and delivery.assigned_to else None,
        },
    )

@login_required
def unassigned_orders(request):
    """List orders that don't have deliveries assigned yet."""
    user = request.user

    if not (user.is_superuser or user.role in ["admin", "pharmacist"]):
        messages.error(request, "You don’t have permission to assign deliveries.")
        return redirect("delivery_list")

    # 🔐 ADMIN / SUPERUSER → see all unassigned orders
    if user.is_superuser:
        orders = Order.objects.filter(delivery__isnull=True)

    # 🔐 PHARMACIST → see ONLY their pharmacy orders
    elif user.role == "pharmacist":
        orders = Order.objects.filter(
            pharmacy=user,
            delivery__isnull=True
        )

    else:
        orders = Order.objects.none()

    return render(request, "unassigned_orders.html", {"orders": orders})


@login_required
def mark_picked(request, pk):
    """Mark a delivery as picked up by the delivery person and send verification code."""
    delivery = get_object_or_404(Delivery, pk=pk, assigned_to=request.user)
    
    # Update status and timestamp
    delivery.status = "picked"
    delivery.picked_at = timezone.now()
    delivery.save()

    # ✅ Generate verification code
    delivery.generate_verification_code()  # Make sure this saves the code in the model

    # ✅ Send code to patient via email
    try:
        print("📩 DEBUG: Sending verification code email...")
        print(f"➡️ Recipient: {delivery.order.patient.email}")
        print(f"➡️ Delivery ID: {delivery.id}")
        print(f"➡️ Verification Code: {delivery.verification_code}")

        subject = f"Your Order #{delivery.order.id} Verification Code"
        message = (
            f"Your verification code for order #{delivery.order.id} is "
            f"{delivery.verification_code}. Please share this only with the delivery agent."
        )

        sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[delivery.order.patient.email],
            fail_silently=False,
        )
        print(f"✅ Email send attempted. Return value: {sent}")

    except Exception as e:
        print("🔥 Email send failed!")
        print("Error type:", type(e).__name__)
        print("Error message:", str(e))
        traceback.print_exc()

    messages.success(request, "Delivery marked as picked and code sent to patient.")
    return redirect("delivery_list")


@login_required
def mark_delivered(request, pk):
    """Mark a delivery as delivered by delivery person."""
    delivery = get_object_or_404(Delivery, pk=pk, assigned_to=request.user)
    delivery.status = "delivered"
    delivery.delivered_at = timezone.now()
    delivery.save()
    messages.success(request, "Delivery marked as delivered.")
    return redirect("delivery_list")


# Track delivery route (simple demo version)
@login_required
def track_route(request, delivery_id):
    delivery = get_object_or_404(Delivery, pk=delivery_id)

    # Pickup coordinates from pharmacy
    pharmacy = delivery.order.pharmacy
    pickup = [pharmacy.latitude, pharmacy.longitude] if pharmacy else None

    # Drop coordinates from order
    drop = [delivery.order.latitude, delivery.order.longitude] if delivery.order.latitude and delivery.order.longitude else None

    if not pickup or not drop:
        messages.error(request, "Coordinates missing. Please check the pharmacy and delivery addresses.")
        return redirect("dashboard")  # update if your URL name is different

    context = {
        "delivery": delivery,
        "pickup": pickup,
        "drop": drop,
    }
    return render(request, "track_route.html", context)


@login_required
def track_order_redirect(request):
    # ✅ Expect order_number from query param
    order_number = request.GET.get("order_number", "").strip().upper()

    if not order_number:
        messages.error(
            request,
            "Please enter a valid Order Number (e.g. ORD-5A1685E2)."
        )
        return redirect("dashboard")

    # ✅ Fetch order safely
    order = get_object_or_404(Order, order_number=order_number)

    # 🔒 SECURITY: Patient can track ONLY their own order
    if request.user.role == "patient" and order.patient != request.user:
        messages.error(request, "You are not authorized to track this order.")
        return redirect("dashboard")

    try:
        # ✅ One-to-one expected between Order and Delivery
        delivery = Delivery.objects.get(order=order)

        return redirect(
            "track_route",
            delivery_id=delivery.id
        )

    except Delivery.DoesNotExist:
        messages.error(
            request,
            "Delivery has not been assigned yet for this order."
        )
        return redirect("dashboard")

    except Delivery.MultipleObjectsReturned:
        messages.error(
            request,
            "System error: multiple deliveries found. Please contact support."
        )
        return redirect("dashboard")

@login_required
def today_deliveries(request):
    today = now().date()
    deliveries = Delivery.objects.filter(
        status="delivered",
        delivered_at__date=today
    ).select_related("order", "order__patient")  # optimization




@login_required
def verify_delivery_code(request, delivery_id):
    """Verify code entered by delivery person before marking delivered."""
    delivery = get_object_or_404(Delivery, pk=delivery_id)

    if request.method == "POST":
        code_entered = request.POST.get("verification_code")

        if code_entered == delivery.verification_code:
            delivery.status = "delivered"
            delivery.delivered_at = timezone.now()
            delivery.save()
            messages.success(request, "Delivery successfully completed!")
        else:
            messages.error(request, "Verification code is incorrect. Delivery not completed.")

    return redirect("delivery_list")


def register_delivery_person(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        raw_password = request.POST['password']   # pharmacist-provided password

        # Create account
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(raw_password),
            role="delivery",     # Custom role field
            is_active=True
        )

        # Send email with login details
        send_mail(
            subject="Your PharmaCare Delivery Account",
            message=(
                f"Hello {username},\n\n"
                f"Your delivery staff account has been created.\n\n"
                f"Login Email: {email}\n"
                f"Password: {raw_password}\n\n"
                f"Please log in and change your password after first login.\n\n"
                f"PharmaCare Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect('delivery_list')

    return render(request, "register_delivery_person.html")