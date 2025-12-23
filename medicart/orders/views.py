
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal


from .models import Order, OrderItem
from shop.models import Medicine
from prescriptions.models import Prescription
from accounts.models import User
from .forms import OrderStatusForm


@login_required
def order_list(request):
    patient_id = request.GET.get("user_id")
    pharmacist_id = request.GET.get("pharmacy_id")
    print("Patient ID:", patient_id)  # Debugging line
    print("Pharmacist ID:", pharmacist_id)  # Debugging line
    user = request.user
    if user.role == "patient":
        orders = Order.objects.filter(patient=user).order_by('-created_at')
    elif user.role == "admin" or user.is_superuser:
        print("Admin accessing order list")  # Debugging line
        if patient_id is not None:
            orders = Order.objects.filter(patient=patient_id)
            
        elif pharmacist_id is not None:
            orders = Order.objects.filter(pharmacy=pharmacist_id)
            print("Filtered by pharmacist ID:", pharmacist_id)  # Debugging line
        else:
            orders = Order.objects.all().order_by('-created_at')    
    elif user.role == "pharmacist":
        orders = Order.objects.filter(pharmacy=user)
    elif user.is_superuser:
        print("Admin accessing order list")  # Debugging line
        if patient_id:
            orders = Order.objects.filter(pharmacist=patient_id)
        else:
            orders = Order.objects.all().order_by('-created_at')            
    else:
        orders = Order.objects.none()

    if patient_id:
        orders = orders.filter(patient=patient_id)

        
        # ---------------- FILTERS ----------------
    order_number = request.GET.get("order_number")
    status = request.GET.get("status")
    payment_status = request.GET.get("payment_status")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if order_number:
        orders = orders.filter(order_number__icontains=order_number)

    if status:
        orders = orders.filter(status=status)

    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    if from_date:
        orders = orders.filter(created_at__date__gte=from_date)

    if to_date:
        orders = orders.filter(created_at__date__lte=to_date)

    orders = orders.order_by("-created_at")


    return render(request, "order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    """Detailed view of a specific order with items."""
    order = get_object_or_404(Order, pk=pk)
    return render(request, "order_detail.html", {"order": order})


@login_required
@transaction.atomic
def create_order(request):
    """Place an order by patient."""
    if request.user.role != "patient":
        messages.error(request, "Only patients can place orders.")
        return redirect("order_list")

    if request.method == "POST":
        pharmacy_id = request.POST.get("pharmacy")
        prescription_id = request.POST.get("prescription")
        delivery_address = request.POST.get("delivery_address")
        medicine_ids = request.POST.getlist("selected_medicines")  # selected medicines

        if not pharmacy_id:
            messages.error(request, "Please select a pharmacy.")
            return redirect("create_order")

        if not medicine_ids:
            messages.error(request, "Please select at least one medicine.")
            return redirect("create_order")

        pharmacy = get_object_or_404(User, id=pharmacy_id)
        prescription = Prescription.objects.filter(id=prescription_id).first() if prescription_id else None

        # Create the order
        order = Order.objects.create(
            patient=request.user,  # ✅ important for order list display
            pharmacy=pharmacy,
            prescription=prescription,
            delivery_address=delivery_address,
            status="pending",
            payment_status="pending"  # ✅ new orders start as pending payment
        )

        total_amount = Decimal("0.00")

        # Add order items
        for med_id in medicine_ids:
            medicine = get_object_or_404(Medicine, id=med_id)
            qty = int(request.POST.get(f"quantity_{med_id}", 1))
            if qty < 1:
                qty = 1

            OrderItem.objects.create(
                order=order,
                medicine=medicine,
                pharmacy=pharmacy,
                quantity=qty,
                price=medicine.price
            )
            total_amount += qty * medicine.price

        order.total_amount = total_amount
        order.save()

        messages.success(request, "Order placed successfully.")
        # Redirect to payment page (or mark as success if payment is instant)
        return redirect("payment_success", order_id=order.id)

    # GET request
    medicines = Medicine.objects.all()
    pharmacies = User.objects.filter(role="pharmacist", approved=True)
    prescriptions = Prescription.objects.filter(patient=request.user)

    return render(request, "create_order.html", {
        "medicines": medicines,
        "pharmacies": pharmacies,
        "prescriptions": prescriptions
    })

@login_required
def update_order_status(request, pk):
    """Pharmacist/Admin can update order status."""
    if not (request.user.role in ["pharmacist", "admin"] or request.user.is_superuser):
        messages.error(request, "You are not authorized to update orders.")
        return redirect("order_list")

    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Order status updated.")
            return redirect("order_detail", pk=pk)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "update_order_status.html", {"form": form, "order": order})



    
