from django import forms
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from orders.models import Order, OrderItem
from prescriptions.models import Prescription
from .models import *
from .forms import *
from accounts.models import *
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import ProtectedError, Q
from geopy.exc import GeocoderTimedOut 
from geopy.geocoders import Nominatim  #type: ignore


# -------------------- PHARMACY --------------------
@login_required
def pharmacy_list(request):
    pharmacies = User.objects.filter(role="pharmacist")
    return render(request, "pharmacy_list.html", {"pharmacies": pharmacies})


@login_required
def pharmacy_detail(request, pk):
    pharmacy = get_object_or_404(User, pk=pk, role="pharmacist")
    return render(request, "pharmacy_detail.html", {"pharmacy": pharmacy})



@login_required
def pharmacy_approve_toggle(request, id):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can approve/reject pharmacies.")
        return redirect("dashboard")

    pharmacy = get_object_or_404(User, id=id, role="pharmacist")
    action = request.GET.get("action")  # either "approve" or "reject"

    if action == "approve":
        pharmacy.approved = True
        messages.success(request, f"{pharmacy.pharmacy_name} has been approved.")
    elif action == "reject":
        pharmacy.approved = False
        messages.warning(request, f"{pharmacy.pharmacy_name} has been rejected.")

    pharmacy.save()
    return redirect("pharmacy_list")

@login_required
def pharmacy_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Only admins can delete pharmacies.")
        return redirect("pharmacy_list")

    pharmacy = get_object_or_404(User, pk=pk, role="pharmacist")

    if request.method == "POST":
        pharmacy.delete()
        messages.success(request, "Pharmacy deleted successfully.")
    return redirect("pharmacy_list")

# -------------------- CATEGORY --------------------
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, "category_list.html", {"categories": categories})


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm()
    return render(request, "category_form.html", {"form": form})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)
    return render(request, "category_form.html", {"form": form})    


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect("category_list")


# views.py
@login_required
def toggle_medicine_status(request, med_id):
    if request.user.role != "admin":
        messages.error(request, "Permission denied.")
        return redirect("medicine_list")

    medicine = get_object_or_404(Medicine, id=med_id)
    medicine.is_active = not medicine.is_active
    medicine.save()

    status = "activated" if medicine.is_active else "deactivated"
    messages.success(request, f"{medicine.name} has been {status}.")
    return redirect("medicine_list")

# -------------------- MEDICINE --------------------
@login_required
def medicine_list(request):
    query = request.GET.get("q", "").strip()
    pharmacy_id = request.GET.get("pharmacy", "")

    # Base queryset
    medicines = Medicine.objects.select_related(
        'category', 'pharmacy'
    )

    # 🔍 Search filter (all roles)
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query)
        )

    # 🔐 Role-based filtering
    if request.user.role == "pharmacist":
        # Pharmacist sees ONLY their own medicines (active + inactive)
        medicines = medicines.filter(
            pharmacy=request.user
        )

    elif request.user.role == "patient":
        # ❌ Patients should NOT see inactive medicines
        medicines = medicines.filter(
            is_active=True,
            pharmacy__approved=True,
            pharmacy__role="pharmacist"
        )

        # Optional pharmacy filter for patients
        if pharmacy_id:
            medicines = medicines.filter(pharmacy_id=pharmacy_id)

    elif request.user.is_superuser or request.user.role == "admin":
        # Admin sees EVERYTHING
        if pharmacy_id:
            medicines = medicines.filter(pharmacy_id=pharmacy_id)

    else:
        # Delivery / others → only active + approved
        medicines = medicines.filter(
            is_active=True,
            pharmacy__approved=True
        )

    # 🏥 Pharmacy dropdown only for admin
    pharmacies = None
    if request.user.is_superuser or request.user.role == "admin":
        pharmacies = User.objects.filter(
            role="pharmacist"
        ).only("id", "pharmacy_name", "username")

    context = {
        "medicines": medicines.order_by("-id"),
        "pharmacies": pharmacies,
        "query": query,
        "pharmacy_id": pharmacy_id,
        "is_admin": request.user.is_superuser or request.user.role == "admin",
        "is_pharmacist": request.user.role == "pharmacist",
    }

    return render(request, "medicine_list.html", context)
@login_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    return render(request, "medicine_detail.html", {"medicine": medicine})


@login_required
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST, request.FILES)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.pharmacy = request.user  # Assuming the logged-in user is the pharmacist
            medicine.save()
            messages.success(request, "Medicine created successfully.")
            return redirect("medicine_list")
    else:
        form = MedicineForm()
    return render(request, "medicine_form.html", {"form": form})


@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        form = MedicineForm(request.POST, request.FILES, instance=medicine)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.pharmacy = request.user  # Assuming the logged-in user is the pharmacist
            medicine.save()
            messages.success(request, "Medicine updated successfully.")
            return redirect("medicine_list")
    else:
        form = MedicineForm(instance=medicine)
    return render(request, "medicine_form.html", {"form": form, "medicine": medicine})
    

def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        try:
            medicine.delete()
            messages.success(request, "Medicine deleted successfully.")
        except ProtectedError:
            messages.error(
                request,
                "❌ Cannot delete this medicine because it is linked to existing orders."
            )
        return redirect("medicine_list")
    return redirect("medicine_list")


# -------------------- STOCK --------------------
@login_required
def stock_list(request):
    user = request.user

    if user.role == "pharmacist":
        stocks = Stock.objects.filter(pharmacy=user)

    elif user.is_superuser:
        pharmacy_id = request.GET.get("pharmacy_id")
        if pharmacy_id:
            stocks = Stock.objects.filter(pharmacy_id=pharmacy_id)
        else:
            stocks = Stock.objects.none()

    else:
        stocks = Stock.objects.none()

    return render(request, "stock_list.html", {"stocks": stocks})


@login_required
def stock_detail(request, pk):
    stock = get_object_or_404(Stock, pk=pk)

    today = date.today()
    expiring_soon = None
    if stock.expiry_date:
        if stock.expiry_date < today:
            expiring_soon = "expired"
        elif stock.expiry_date <= today + timedelta(days=30):
            expiring_soon = "expiring"
        else:
            expiring_soon = "valid"

    return render(request, "stock_detail.html", {
        "stock": stock,
        "expiry_status": expiring_soon,
        "today": today,
    })

@login_required
def stock_create(request):
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)  # Don't save yet
            stock.pharmacy = stock.medicine.pharmacy  # Assign pharmacy from selected medicine
            
            stock.save()  # Now save
            messages.success(request, "Stock entry created successfully.")
            return redirect("stock_list")
    else:
        form = StockForm()
    return render(request, "stock_form.html", {"form": form})

@login_required
def stock_update(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, "Stock updated successfully.")
            return redirect("stock_list")
    else:
        form = StockForm(instance=stock)
    return render(request, "stock_form.html", {"form": form, "stock": stock})

@login_required
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        stock.delete()
        messages.success(request, "Stock entry deleted successfully.")
        return redirect("stock_list")
    return render(request, "stock_confirm_delete.html", {"stock": stock})

# -------------------- CART & CHECKOUT --------------------
@login_required
def add_multiple_to_cart(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_medicines")
        if selected_ids:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            for med_id in selected_ids:
                medicine = get_object_or_404(Medicine, id=med_id)
                item, created = CartItem.objects.get_or_create(cart=cart, medicine=medicine)
                if not created:
                    item.quantity += 1
                    item.save()
        return redirect("view_cart")
    return redirect("medicine_list")

@login_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect("view_cart")


@login_required
def update_cart(request):
    if request.method == "POST":
        cart = get_user_cart(request.user)
        for item in cart.items.all():
            qty = request.POST.get(f"quantity_{item.id}")
            if qty:
                item.quantity = int(qty)
                item.save()
        messages.success(request, "Cart updated successfully.")
    return redirect("view_cart")


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart.html", {"cart": cart})

@login_required
def checkout(request):
    cart = get_user_cart(request.user)

    # ✅ STEP 1: Check if cart has prescription-required medicines
    rx_items = cart.items.filter(
        medicine__prescription_required=True
    )

    # ✅ STEP 2: If patient + Rx items → require VERIFIED prescription
    if rx_items.exists() and request.user.role == "patient":
        prescription = Prescription.objects.filter(
            patient=request.user,
            verified=True,
            used=False
        ).last()

        if not prescription:
            messages.error(
                request,
                "A valid prescription is required to proceed with checkout."
            )
            return redirect("view_cart")

    # -----------------------------------------
    # Continue checkout normally
    # -----------------------------------------
    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        delivery_address = request.POST.get("delivery_address")

        medicines_data = [
            {
                "id": item.medicine.id,
                "quantity": item.quantity,
            }
            for item in cart.items.all()
        ]




        request.session['checkout_data'] = {
            "medicines": medicines_data,
            "delivery_address": delivery_address,
            "payment_method": payment_method,
            "prescription_id": prescription.id if prescription else None
        }

        return redirect("payment_success")

    return render(request, "checkout.html", {"cart": cart})


def get_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

@login_required
@transaction.atomic
def payment_success(request):
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.error(request, "No checkout data found.")
        return redirect("medicine_list")

    prescription = None
    if checkout_data.get('prescription_id'):
        prescription = Prescription.objects.filter(id=checkout_data['prescription_id']).first()

    delivery_address = checkout_data.get('delivery_address', '')
    prescription_id = checkout_data.get('prescription_id')

    if prescription_id:
        prescription = Prescription.objects.select_for_update().filter(
            id=prescription_id,
            patient=request.user,
            verified=True,
            used=False
        ).first()

     # 🟢 Determine pharmacy from first medicine
    first_medicine = get_object_or_404(Medicine, id=checkout_data['medicines'][0]['id'])
    pharmacy = first_medicine.pharmacy
    
    # ✅ Create Order
    order = Order.objects.create(
        patient=request.user,
        prescription=prescription,
        pharmacy=pharmacy,
        delivery_address=delivery_address,
        status='pending',
        payment_status='paid'
    )

    # ✅ Try geocoding the delivery address
    try:
        geolocator = Nominatim(user_agent="pharmacy_app")
        location = geolocator.geocode(delivery_address, timeout=10)
        if location:
            order.latitude = location.latitude
            order.longitude = location.longitude
            order.save(update_fields=["latitude", "longitude"])
    except GeocoderTimedOut:
        print("⚠️ Geocoding timed out; skipping coordinate assignment.")

    total_amount = Decimal("0.00")

    for med in checkout_data['medicines']:
        medicine = get_object_or_404(Medicine, id=med['id'])
        qty = med.get('quantity', 1)

        # ✅ Reduce stock
        try:
            stock = Stock.objects.get(medicine=medicine, pharmacy=medicine.pharmacy)
            if stock.quantity >= qty:
                stock.quantity -= qty
                stock.save()
            else:
                transaction.set_rollback(True)
                messages.error(request, f"Not enough stock for {medicine.name}.")
                return redirect("view_cart")
        except Stock.DoesNotExist:
            transaction.set_rollback(True)
            messages.error(request, f"No stock available for {medicine.name}.")
            return redirect("view_cart")

        # ✅ Create order item
        OrderItem.objects.create(
            order=order,
            medicine=medicine,
            pharmacy=medicine.pharmacy,
            quantity=qty,
            price=medicine.price
        )

        total_amount += qty * medicine.price

    order.total_amount = total_amount
    order.save()

    if prescription:
        prescription.used = True
        prescription.save(update_fields=["used"])

    # ✅ Clear cart
    cart = get_user_cart(request.user)
    cart.items.all().delete()

    # ✅ Clear session
    request.session.pop('checkout_data', None)

    return render(request, "payment_success.html", {"order": order})