from django.db import models
from django.conf import settings
from django.utils import timezone

class Customer(models.Model):
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
        """Update customer booking statistics"""
        from bookings.models import Booking
        bookings = Booking.objects.filter(customer=self)
        
        self.total_bookings = bookings.count()
        self.total_spent = sum(booking.total_amount for booking in bookings.filter(payment_status='Paid'))
        
        latest_booking = bookings.order_by('-start_date').first()
        if latest_booking:
            self.last_booking_date = latest_booking.start_date
            
        self.save(update_fields=['total_bookings', 'total_spent', 'last_booking_date'])
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['phone_number']),
        ]
