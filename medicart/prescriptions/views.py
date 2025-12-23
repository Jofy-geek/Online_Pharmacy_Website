from django.shortcuts import render

# Create your views here.
import pytesseract  # type: ignore
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Prescription
from .forms import PrescriptionForm  # we'll create a form
from shop.models import Cart

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def normalize_text(text):
    """Normalize text by converting to lowercase and removing extra whitespace."""
    return ' '.join(text.lower().split())

@login_required
def prescription_list(request):
    """Patients see their own prescriptions, pharmacists/admins see all."""
    if request.user.role == "patient":
        prescriptions = Prescription.objects.filter(patient=request.user)
        
    elif request.user.role == "pharmacist":
        prescriptions = Prescription.objects.filter(
            order__pharmacy=request.user
        ).distinct()    
    elif request.user.is_superuser:
        prescriptions = Prescription.objects.all()

    else:
        prescriptions = Prescription.objects.none()

    return render(request, "prescription_list.html", {"prescriptions": prescriptions})


@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    return render(request, "prescription_detail.html", {"prescription": prescription})



@login_required
def upload_prescription(request):
    print("Upload prescription view called")
    """Patient uploads a prescription."""
    if request.user.role != "patient":
        messages.error(request, "Only patients can upload prescriptions.")
        return redirect("prescription_list")
    print(request.method,"method")
    if request.method == "POST":
        form = PrescriptionForm(request.POST, request.FILES)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.patient = request.user
            prescription.verified = False
            prescription.save()

            try:
                image = Image.open(prescription.uploaded_file.path)
                extracted_text = pytesseract.image_to_string(image)

                normalized_ocr = normalize_text(extracted_text)

                # 🔍 Get Rx medicines from cart
                cart = Cart.objects.get(user=request.user)
                rx_items = cart.items.filter(
                    medicine__prescription_required=True
                )

                unmatched = []

                for item in rx_items:
                    medicine_name = normalize_text(item.medicine.name)
                    print("Checking medicine:", medicine_name,'in',normalized_ocr)
                    if medicine_name not in normalized_ocr:
                        unmatched.append(item.medicine.name)

                # ✅ Decide verification
                if unmatched:
                    prescription.notes = extracted_text
                    prescription.save()
                    messages.error(
                        request,
                        f"Prescription does not include: {', '.join(unmatched)}"
                    )
                else:
                    prescription.notes = extracted_text
                    prescription.verified = True
                    prescription.save()
                    messages.success(
                        request,
                        "Prescription verified successfully."
                    )

            except Exception as e:
                messages.error(request, f"OCR failed: {e}")

            return redirect("view_cart")

    else:
        print("GET method called")
        form = PrescriptionForm()

    return render(request, "upload_prescription.html", {"form": form})


@login_required
def verify_prescription(request, pk):
    """Pharmacist/Admin verifies a prescription."""
    if not (request.user.role in ["pharmacist", "admin"] or request.user.is_superuser):
        messages.error(request, "Not authorized to verify prescriptions.")
        return redirect("prescription_list")

    prescription = get_object_or_404(Prescription, pk=pk)

    if request.method == "POST":
        prescription.verified = True
        prescription.verified_by = request.user
        prescription.save()
        messages.success(request, "Prescription verified successfully.")
        return redirect("prescription_detail", pk=pk)

    return render(request, "verify_prescription.html", {"prescription": prescription})
