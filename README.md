# Medicart - Smart Online Pharmacy System

A comprehensive Django-based e-pharmacy platform that enables patients to order medicines online, pharmacists to manage their inventory, and delivery staff to handle order fulfillment. The system includes prescription verification, real-time inventory management, delivery tracking, and role-based dashboards.

## 🚀 Features

### Core Modules

- **👥 Multi-Role User Management**
  - Patient, Pharmacist, Admin, and Delivery Staff roles
  - Role-based access control and dashboards
  - User approval workflow (pharmacists require admin approval)
  - Profile management with auto-geocoding

- **🏥 Pharmacy Management**
  - Pharmacy registration and listing
  - Admin approval/rejection system
  - Location tracking (latitude/longitude)
  - Pharmacy detail pages

- **💊 Medicine Catalog**
  - Complete CRUD operations for medicines
  - Medicine categorization and search
  - Prescription requirement flagging
  - Medicine images and expiry date tracking
  - Brand and SKU management
  - Role-based visibility control

- **📦 Stock Management**
  - Real-time stock tracking per pharmacy
  - Low stock threshold alerts
  - Expiry date monitoring
  - Automatic stock deduction on order creation
  - Unique constraint per medicine-pharmacy combination

- **📋 Prescription Management**
  - Prescription upload by patients
  - OCR (Optical Character Recognition) using Tesseract
  - Prescription verification by pharmacists/admins
  - Prescription-to-order linking
  - Prescription notes storage

- **🛒 Shopping Cart**
  - Add multiple medicines to cart
  - Cart item management (add/remove/update)
  - Cart total calculation
  - Prescription validation before checkout

- **📦 Order Management**
  - Order creation from cart
  - Order status workflow (Pending → Confirmed → Processing → Out for Delivery → Delivered → Cancelled)
  - Payment status tracking (Pending/Paid/Failed)
  - Multiple payment methods (COD, Card, UPI)
  - Role-based order visibility

- **🚚 Delivery Management**
  - Delivery assignment to delivery staff
  - Delivery status tracking
  - Pick-up and delivery timestamps
  - Verification code system for secure delivery
  - Route tracking with geocoding
  - Distance and expected delivery time calculation
  - On-time delivery rate tracking

- **📊 Role-Based Dashboards**
  - **Patient Dashboard**: Active orders, recent prescriptions
  - **Pharmacist Dashboard**: Pending orders, pending prescriptions, low stock alerts, monthly sales
  - **Admin Dashboard**: Total users, pharmacies, orders, categories, system alerts
  - **Delivery Dashboard**: Pending deliveries, completed deliveries today, on-time rate, latest delivery

- **📧 Email Notifications**
  - Verification code emails to patients
  - Delivery person account creation emails
  - Password reset emails

## 🛠️ Technology Stack

- **Backend**: Django 4.2.25
- **Database**: SQLite3 (development)
- **Frontend**: Django Templates (HTML/CSS/JavaScript)
- **External Services**:
  - Tesseract OCR (prescription text extraction)
  - Geopy/Nominatim (geocoding)
  - SMTP (email notifications)
- **Additional Libraries**:
  - Pillow (image processing)
  - Django REST Framework (API capability)
  - Django Widget Tweaks (form styling)
  - pytesseract (OCR integration)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9 or higher
- pip (Python package manager)
- Tesseract OCR (for prescription text extraction)
  - **Windows**: Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - **macOS**: `brew install tesseract`
  - **Linux**: `sudo apt-get install tesseract-ocr`

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Online_Pharmacy_Website/medicart
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate the virtual environment**
   - **Windows**:
     ```bash
     env\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source env/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files** (if needed)
   ```bash
   python manage.py collectstatic
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## ⚙️ Configuration

### Email Settings

Update email configuration in `medicart/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

**Note**: For Gmail, you'll need to generate an App Password. Go to your Google Account settings → Security → 2-Step Verification → App passwords.

### Tesseract OCR Path

If Tesseract is not in your system PATH, configure the path in your code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows example
```

### Database Configuration

For production, update the database settings in `medicart/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📁 Project Structure

```
medicart/
├── accounts/              # User authentication and management
│   ├── models.py         # User model with roles
│   ├── views.py          # Authentication views
│   ├── forms.py          # User registration/login forms
│   └── templates/        # User-related templates
├── shop/                 # Medicine catalog and shopping
│   ├── models.py         # Category, Medicine, Stock, Cart models
│   ├── views.py          # Shop views
│   └── templates/        # Shop templates
├── orders/               # Order management
│   ├── models.py         # Order, OrderItem models
│   ├── views.py          # Order views
│   └── templates/        # Order templates
├── prescriptions/        # Prescription management
│   ├── models.py         # Prescription model
│   ├── views.py          # Prescription views
│   └── templates/        # Prescription templates
├── deliveries/           # Delivery management
│   ├── models.py         # Delivery model
│   ├── views.py          # Delivery views
│   └── templates/        # Delivery templates
├── medicart/             # Django project settings
│   ├── settings.py       # Project configuration
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── media/                # User-uploaded files
├── manage.py             # Django management script
└── requirements.txt      # Python dependencies
```

## 👥 User Roles

### Patient (Public User)
- Browse and search medicines
- Add medicines to cart
- Upload prescriptions
- Place orders
- Track orders
- View order history

### Pharmacist
- Register pharmacy (requires admin approval)
- Add/manage medicines
- Manage stock inventory
- View and process orders
- Verify prescriptions
- View sales analytics

### Admin
- Approve/reject pharmacists
- Approve/reject pharmacies
- Manage all users
- View all orders and deliveries
- Manage categories
- System-wide analytics
- Assign deliveries

### Delivery Staff
- View assigned deliveries
- Mark pickups and deliveries
- Track delivery routes
- Verify delivery codes
- View delivery statistics

## 🔄 Key Workflows

### 1. User Registration & Approval
- Patients/Delivery Staff: Auto-approved
- Pharmacists: Require admin approval
- Admin: Auto-approved

### 2. Order Processing
1. Patient adds medicines to cart
2. System validates prescription requirements
3. Patient checks out and selects payment method
4. Order created with "Pending" status
5. Pharmacist confirms order
6. Order status changes to "Processing"
7. Admin/Pharmacist assigns delivery person
8. Delivery person picks up order
9. Order status changes to "Out for Delivery"
10. Delivery person delivers with verification code
11. Order status changes to "Delivered"

### 3. Prescription Processing
1. Patient uploads prescription image
2. OCR extracts text from prescription
3. Pharmacist/Admin reviews and verifies
4. Verified prescription linked to order
5. Order can proceed with prescription-required medicines

### 4. Stock Management
1. Pharmacist adds medicine to catalog
2. Pharmacist creates stock entry with quantity
3. System tracks stock levels
4. Low stock alerts generated when threshold reached
5. Stock automatically deducted on order creation
6. Expiry dates monitored

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in `settings.py`
- [ ] Update `SECRET_KEY` with a secure random key
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up a production database (PostgreSQL recommended)
- [ ] Configure static files serving
- [ ] Set up SSL/HTTPS
- [ ] Configure email backend
- [ ] Set up proper logging
- [ ] Configure media file storage (AWS S3, etc.)
- [ ] Set up backup strategy

### Environment Variables

For production, use environment variables for sensitive settings:

```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

## 📝 API Documentation

The project uses Django REST Framework. API endpoints are available at `/api/` (if configured).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Medicart Development Team**

## 🙏 Acknowledgments

- Django community for excellent documentation
- Tesseract OCR team
- Geopy library contributors
- All open-source libraries used in this project

## 📞 Support

For support, email support@medicart.com or create an issue in the repository.

## 🔒 Security

- **Important**: Change the `SECRET_KEY` in production
- Never commit sensitive credentials to version control
- Use environment variables for sensitive configuration
- Keep dependencies updated
- Regularly review and update security settings

---

**Note**: This is a development version. For production deployment, ensure all security best practices are followed.

