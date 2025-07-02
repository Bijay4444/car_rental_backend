# 🚗 Car Rental Management System

A comprehensive Django REST API backend for managing car rental operations with real-time notifications, booking management, payment processing, and staff coordination.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [🐳 Docker Development Setup](#docker-development-setup)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Real-time Notifications](#real-time-notifications)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🏢 Core Business Features

- **Car Management**: Add, update, and track vehicle inventory
- **Customer Management**: Complete customer profiles with documents
- **Booking System**: Advanced booking with date validation and conflict prevention
- **Payment Processing**: Multiple payment methods with tracking
- **Staff Management**: Role-based access for rental company staff

### 🔔 Real-time Notifications

- **Global Staff Notifications**: All staff receive booking/payment alerts
- **Firebase Cloud Messaging**: Push notifications to mobile devices
- **Multi-device Support**: Multiple devices per staff member
- **Event-driven Alerts**: Automatic notifications on booking changes

### 📊 Advanced Features

- **Booking Extensions**: Extend rental periods
- **Car Swapping**: Change vehicles during active rentals
- **Accident Reporting**: Document and track vehicle incidents
- **Overdue Management**: Track and manage late returns
- **Financial Tracking**: Comprehensive payment and billing system

## 🛠 Tech Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL/SQLite
- **Authentication**: JWT with Simple JWT
- **Notifications**: Firebase Cloud Messaging (FCM)
- **Documentation**: MkDocs, Swagger/OpenAPI, ReDoc
- **File Storage**: Django Media Files
- **Deployment**: Gunicorn, Docker-ready

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git
- Firebase Project (for notifications)
- PostgreSQL (optional, SQLite by default)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/car-rental-management.git
cd car-rental-management
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (Optional - uses SQLite by default)
DATABASE_URL=postgresql://username:password@localhost:5432/car_rental_db

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# Media Files
MEDIA_URL=/media/
MEDIA_ROOT=media/
```

### 5. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic
```

## ⚙️ Configuration

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Cloud Messaging
4. Generate service account key:
   - Project Settings → Service Accounts
   - Generate new private key
   - Add credentials to `.env` file

### Database Configuration

**SQLite (Default)**:
No additional setup required.

**PostgreSQL**:

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Create database
createdb car_rental_db

# Update DATABASE_URL in .env
```

## 📚 API Documentation

### Documentation Options

Your API documentation is available in multiple formats:

#### 1. **Swagger UI** (Interactive)

```
http://127.0.0.1:8080/swagger/
```

- Interactive API testing
- Request/response examples
- Authentication testing

#### 2. **ReDoc** (Clean Documentation)

```
http://127.0.0.1:8080/redoc/
```

- Clean, readable documentation
- Better for reference
- Mobile-friendly

#### 3. **MkDocs** (Comprehensive Guide)

```bash
# Install MkDocs (if not already installed)
pip install mkdocs mkdocs-material

# Serve documentation
mkdocs serve

# View at: http://127.0.0.1:8000
```

#### 4. **Django Admin** (Management Interface)

```
http://127.0.0.1:8080/admin/
```

## 🏃‍♂️ Running the Application

### Development Server

```bash
python manage.py runserver 8080
```

Access the application:

- **API Base**: http://127.0.0.1:8080/api/
- **Admin Panel**: http://127.0.0.1:8080/admin/
- **API Docs**: http://127.0.0.1:8080/swagger/

### Production Deployment

```bash
# Using Gunicorn
gunicorn car_management_system.wsgi:application --bind 0.0.0.0:8080

# Or using the provided script
./deploy.sh
```

## 🔗 API Endpoints

### Authentication

```
POST /api/auth/register/          # Staff registration
POST /api/auth/login/             # Login
POST /api/auth/logout/            # Logout
POST /api/auth/change-password/   # Password change
GET  /api/auth/profile/           # User profile
```

### Cars Management

```
GET    /api/cars/                 # List all cars
POST   /api/cars/                 # Add new car
GET    /api/cars/{id}/            # Car details
PUT    /api/cars/{id}/            # Update car
DELETE /api/cars/{id}/            # Delete car
GET    /api/cars/available/       # Available cars
```

### Customers

```
GET    /api/customers/            # List customers
POST   /api/customers/            # Add customer
GET    /api/customers/{id}/       # Customer details
PUT    /api/customers/{id}/       # Update customer
DELETE /api/customers/{id}/       # Delete customer
```

### Bookings

```
GET    /api/bookings/             # List bookings
POST   /api/bookings/             # Create booking
GET    /api/bookings/{id}/        # Booking details
PUT    /api/bookings/{id}/        # Update booking
DELETE /api/bookings/{id}/        # Cancel booking

# Booking Actions
POST   /api/bookings/{id}/cancel/      # Cancel booking
POST   /api/bookings/{id}/return/      # Return car
POST   /api/bookings/{id}/extend/      # Extend booking
POST   /api/bookings/{id}/swap/        # Swap car
POST   /api/bookings/{id}/accident/    # Report accident
```

### Payments

```
GET    /api/payments/             # List payments
POST   /api/payments/             # Record payment
GET    /api/payments/{id}/        # Payment details
PUT    /api/payments/{id}/        # Update payment
```

### Notifications

```
GET    /api/notifications/preferences/     # Get preferences
PUT    /api/notifications/preferences/     # Update preferences
POST   /api/notifications/save-fcm-token/  # Save device token
POST   /api/notifications/test-push/       # Test notification
GET    /api/notifications/devices/         # List user devices
DELETE /api/notifications/devices/         # Remove device
```

## 🔔 Real-time Notifications

### How It Works

1. **Staff registers FCM token** via mobile app
2. **System automatically sends notifications** on:
   - New bookings created
   - Payments received
   - Booking cancellations
   - Car returns
   - Overdue alerts

### Multi-device Support

Each staff member can have **multiple devices** registered. All devices receive notifications simultaneously.

### Testing Notifications

```json
POST /api/notifications/test-push/
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
    "send_global": true,
    "title": "Test Notification",
    "body": "Testing global notification system",
    "data": {
        "test": true,
        "priority": "normal"
    }
}
```

### Notification Events

| Event             | Trigger                     | Recipients |
| ----------------- | --------------------------- | ---------- |
| New Booking       | Booking created             | All staff  |
| Payment Received  | Payment recorded            | All staff  |
| Booking Cancelled | Status changed to cancelled | All staff  |
| Car Returned      | Booking marked as returned  | All staff  |
| Overdue Alert     | Daily automated check       | All staff  |

## 🧪 Testing

### Manual API Testing

Use the interactive Swagger UI at `/swagger/` for testing endpoints.

### Postman Collection

Import the API endpoints using the OpenAPI schema:

```
http://127.0.0.1:8080/api/schema/
```

### Sample Test Scenarios

#### 1. Complete Booking Flow

```bash
# 1. Create customer
POST /api/customers/

# 2. Create booking
POST /api/bookings/

# 3. Process payment
POST /api/payments/

# 4. Return car
POST /api/bookings/{id}/return/
```

#### 2. Notification Testing

```bash
# 1. Save FCM token
POST /api/notifications/save-fcm-token/

# 2. Test global notification
POST /api/notifications/test-push/

# 3. Create booking (triggers auto-notification)
POST /api/bookings/
```

### Running Tests

```bash
# Run Django tests
python manage.py test

# Run specific app tests
python manage.py test notifications
python manage.py test bookings
```

## 🚀 Deployment

### Production Setup

1. **Set Production Environment**

```bash
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

2. **Database Migration**

```bash
python manage.py migrate --settings=car_management_system.settings.production
```

3. **Collect Static Files**

```bash
python manage.py collectstatic --noinput
```

4. **Start Production Server**

```bash
gunicorn car_management_system.wsgi:application \
    --bind 0.0.0.0:8080 \
    --workers 3 \
    --timeout 120
```

### Docker Deployment

```dockerfile
# Dockerfile included in repository
docker build -t car-rental-api .
docker run -p 8080:8080 car-rental-api
```

### Environment Variables for Production

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost:5432/car_rental_prod
FIREBASE_PROJECT_ID=your-prod-firebase-project
SECRET_KEY=your-super-secret-production-key
```

## 📱 Mobile App Integration

### Flutter Integration

Your API is designed to work seamlessly with Flutter mobile apps:

1. **Authentication**: JWT token-based
2. **Real-time notifications**: FCM integration
3. **File uploads**: Image handling for profiles and documents
4. **Offline support**: RESTful design for caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Write tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**1. Notifications not working?**

- Check Firebase configuration
- Verify FCM token is saved
- Confirm app permissions

**2. Database errors?**

- Run migrations: `python manage.py migrate`
- Check database connection
- Verify environment variables

**3. Authentication issues?**

- Check JWT token expiration
- Verify user permissions
- Confirm endpoint access

## 📊 Project Statistics

- **Backend**: Django REST Framework
- **Database Models**: 8+ models
- **API Endpoints**: 50+ endpoints
- **Real-time Features**: FCM notifications
- **Documentation**: Swagger, ReDoc, MkDocs
- **Testing**: Comprehensive API testing suite

---

**Made with ❤️ for efficient car rental management**

---

### Quick Start Commands

```bash
# Complete setup in 5 minutes
git clone https://github.com/yourusername/car-rental-management.git
cd car-rental-management
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8080

# Visit: http://127.0.0.1:8080/swagger/
```

🎉 **Your car rental management system is ready to go!**

## 🐳 Docker Development Setup

### Quick Start with Docker

For the fastest development setup using Docker:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/car-rental-management.git
cd car-rental-management

# 2. Create environment file
cp .env.example .env.docker
# Edit .env.docker with your settings

# 3. Start with Docker
docker-compose up -d

# 4. Access application
# Admin Panel: http://localhost:8080/admin/
# API Docs: http://localhost:8080/swagger/
# Database: localhost:5433 (external port)
```

### Docker Architecture

```mermaid
graph TB
    A[Nginx :80] --> B[Django Web :8080]
    B --> C[PostgreSQL :5432]
    B --> D[Redis :6379]
    E[Docker Volumes] --> C
    E --> D
    F[Local Files] --> G[Media /media]
    F --> H[Static /staticfiles]
```

### Services Overview

| Service   | Internal Port | External Port | Purpose                      |
| --------- | ------------- | ------------- | ---------------------------- |
| **nginx** | 80            | 80            | Reverse proxy & static files |
| **web**   | 8080          | 8080          | Django application server    |
| **db**    | 5432          | 5433          | PostgreSQL database          |
| **redis** | 6379          | 6380          | Caching & sessions           |

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web
docker-compose logs -f db

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build web
docker-compose restart web

# Reset everything (⚠️ loses data)
docker-compose down --volumes
docker-compose up -d

# Execute commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic

# Database access
docker-compose exec db psql -U postgres -d car_rental_management

# Container shell access
docker-compose exec web bash
```

### Development Workflow with Docker

#### 🔄 **For Code Changes:**

```bash
# Method 1: Restart service (for small changes)
docker-compose restart web

# Method 2: Rebuild (for dependency changes)
docker-compose build web
docker-compose restart web
```

#### 🗄️ **For Database Operations:**

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load sample data
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

#### 📁 **File Syncing:**

- **Media files**: `./media` ↔ `/app/media` (real-time sync)
- **Static files**: `./staticfiles` ↔ `/app/staticfiles` (real-time sync)
- **Source code**: Copied during build (rebuild required for changes)

### Docker Environment Variables

Create `.env.docker` file:

```env
# Django Settings
DJANGO_SECRET_KEY=your-docker-secret-key
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (Docker)
DB_HOST=db
DB_PORT=5432
DB_NAME=car_rental_management
DB_USER=*******
DB_PASSWORD=********
DB_ENGINE=django.db.backends.postgresql_psycopg2

# Redis (Docker)
REDIS_URL=redis://redis:6379/0

# Firebase Configuration
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Troubleshooting Docker

#### **🔧 Common Issues:**

**1. Port conflicts:**

```bash
# Check what's using ports
sudo netstat -tulpn | grep :8080
sudo netstat -tulpn | grep :5433

# Change ports in docker-compose.yml if needed
```

**2. Database connection errors:**

```bash
# Check database health
docker-compose exec db pg_isready -U postgres

# View database logs
docker-compose logs db

# Reset database
docker-compose down
docker volume rm car_rental_postgres_data
docker-compose up -d
```

**3. Permission errors:**

```bash
# Fix file permissions
sudo chown -R $USER:$USER ./media ./staticfiles

# Fix container permissions
docker-compose exec web chown -R appuser:appuser /app/media /app/staticfiles
```

**4. Container won't start:**

```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

### Production Deployment (Non-Docker)

While Docker is excellent for development, for production deployment on shared hosting (cPanel), you'll need traditional deployment:

```bash
# 1. Prepare production files
zip -r car_rental_production.zip . \
  --exclude="venv/*" \
  --exclude="docker-compose.yml" \
  --exclude="Dockerfile" \
  --exclude=".env.docker"

# 2. Upload to cPanel and configure
# 3. Set up production database
# 4. Update settings.py for production
```

> **💡 Note**: Docker is for development convenience. Production deployment depends on your hosting provider's capabilities.
> hosted on https://fuzionsautoapp.com/
