from django.db import models
from django.conf import settings
from django.utils import timezone

class Customer(models.Model):
    """
    Model representing a customer in the car rental system.

    Stores personal information, identification, status, analytics, and audit fields.

    Attributes:
        profile_image (ImageField): Optional profile image.
        name (str): Customer's full name.
        email (str): Unique email address.
        phone_number (str): Contact phone number.
        gender (str): Gender of the customer.
        date_of_birth (date): Date of birth.
        address (str): Address.
        identification_image (ImageField): Optional ID image.
        status (str): Account status (Active, Blocked, Inactive).
        user (User): Linked user account (optional).
        total_bookings (int): Number of bookings.
        total_spent (Decimal): Total amount spent.
        last_booking_date (date): Date of last booking.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        created_by (User): User who created the record.
    """
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Blocked', 'Blocked'),
        ('Inactive', 'Inactive')
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'), 
        ('Female', 'Female'), 
        ('Other', 'Other')
    ]
    
    # Personal Information
    profile_image = models.ImageField(upload_to='customer_profiles/', blank=True, null=True)
    name = models.CharField(max_length=100, db_index=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    address = models.TextField()
    
    # Identification and Status
    identification_image = models.ImageField(upload_to='customer_ids/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', db_index=True)
    
    # For system integration (if a customer wants to create an account)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='customer_profile')
    
    # Statistics/Analytics
    total_bookings = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_booking_date = models.DateField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, related_name='customers_created')
    
    def update_booking_stats(self):
        """
        Update customer booking statistics.

        Calculates total bookings, total spent, and last booking date.
        """
        from bookings.models import Booking
        bookings = Booking.objects.filter(customer=self)
        
        self.total_bookings = bookings.count()
        self.total_spent = sum(booking.total_amount for booking in bookings.filter(payment_status='Paid'))
        
        latest_booking = bookings.order_by('-start_date').first()
        if latest_booking:
            self.last_booking_date = latest_booking.start_date
            
        self.save(update_fields=['total_bookings', 'total_spent', 'last_booking_date'])
    
    def __str__(self):
        """
        Return the string representation of the customer.

        Returns:
            str: Customer's name.
        """
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['phone_number']),
        ]
