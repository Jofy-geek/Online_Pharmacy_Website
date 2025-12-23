from django import forms
from .models import User
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re

# ----------------- Register Form -----------------
class RegisterForm(forms.ModelForm):
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Enter your password"
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Confirm password"
            }
        )
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'pharmacy_name', "username", "email", "phone", "address", "password1", "password2", "role"]

    def clean_first_name(self):
        name = self.cleaned_data.get("first_name", "").strip()
        if not name:
            raise ValidationError("First name is required.")
        if len(name) < 2:
            raise ValidationError("First name must be at least 2 characters.")
        return name

    def clean_last_name(self):
        name = self.cleaned_data.get("last_name", "").strip()
        if not name:
            raise ValidationError("Last name is required.")
        return name

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username is required.")
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username already taken.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return phone  # phone optional — keep blank allowed
        # basic validation: digits, plus, spaces and - allowed; length 7-20
        if not re.match(r'^[\d\+\-\s\(\)]{7,20}$', phone):
            raise ValidationError("Enter a valid phone number (7-20 characters).")
        return phone

    def clean_pharmacy_name(self):
        name = (self.cleaned_data.get("pharmacy_name") or "").strip()
        role = self.cleaned_data.get("role")
        if role == "pharmacist" and not name:
            raise ValidationError("Pharmacy name is required for pharmacists.")
        # allow blank for non-pharmacist
        return name

    def clean_password1(self):
        p1 = self.cleaned_data.get("password1")
        if not p1:
            raise ValidationError("Password is required.")
        # use Django password validators (length, complexity etc.)
        try:
            validate_password(p1, user=None)
        except ValidationError as e:
            raise ValidationError(e.messages)
        return p1

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        # ensure role is valid
        role = cleaned_data.get("role")
        if role not in dict(User.ROLE_CHOICES).keys():
            raise ValidationError("Invalid role selected.")
        return cleaned_data

    def save(self, commit=True):
        # Save model fields then set password correctly
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


# ----------------- Login Form -----------------
class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Enter your username"
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Enter your password"
            }
        )
    )


# ----------------- Password Reset Request Form -----------------
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Enter your registered email"
            }
        )
    )


# ----------------- Set New Password Form -----------------
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Enter new password"
            }
        )
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Confirm new password"
            }
        )
    )


class ProfileUpdateForm(forms.ModelForm):
    # Optional password fields
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg rounded-3",
            "placeholder": "Enter new password"
        }),
        required=False,
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg rounded-3",
            "placeholder": "Confirm new password"
        }),
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "phone", "address",
            "pharmacy_name"  # Only shown for pharmacists
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 5, "placeholder": "Full address with city & state"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make pharmacy_name required only for pharmacists
        if self.instance.role == "pharmacist":
            self.fields["pharmacy_name"].required = True
            self.fields["pharmacy_name"].help_text = "Your registered pharmacy name (visible to patients)"
        else:
            self.fields["pharmacy_name"].required = False
            self.fields["pharmacy_name"].widget = forms.HiddenInput()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_new_password1(self):
        password1 = self.cleaned_data.get("new_password1")
        if password1:
            try:
                validate_password(password1, user=self.instance)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Passwords do not match.")
        elif p1 and not p2:
            self.add_error("new_password2", "Please confirm your new password.")
        elif p2 and not p1:
            self.add_error("new_password1", "Please enter your new password twice.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Update password if provided
        new_password = self.cleaned_data.get("new_password1")
        if new_password:
            user.set_password(new_password)

        if commit:
            user.save()
        return user