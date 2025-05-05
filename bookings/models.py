from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid

class Booking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Partial', 'Partial'),
        ('Unpaid', 'Unpaid'),
    ]
    
    BOOKING_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled'),
        ('Overdue', 'Overdue'),
    ]
    
    # Booking Identifiers
    booking_id = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    
    # Relationships
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='bookings')
    car = models.ForeignKey('cars.Car', on_delete=models.CASCADE, related_name='bookings')
    
    # Dates and times
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    pickup_time = models.TimeField()
    dropoff_time = models.TimeField()
    actual_return_date = models.DateField(null=True, blank=True, 
                                        help_text="The date when car was actually returned")
    
    # Status information
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, 
                                    default='Active', db_index=True)
    car_returned = models.BooleanField(default=False)
    
    # Payment details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, 
                                    default='Unpaid', db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, 
                                 help_text="Base fee * number of days")
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extension_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                         help_text="Additional charges if booking was extended")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, null=True, blank=True)
    
    # Accident information
    has_accident = models.BooleanField(default=False)
    accident_description = models.TextField(blank=True, null=True)
    accident_date = models.DateField(null=True, blank=True)
    accident_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Car swap feature
    original_car = models.ForeignKey('cars.Car', on_delete=models.SET_NULL, null=True, 
                                   blank=True, related_name='original_bookings')
    has_been_swapped = models.BooleanField(default=False)
    swap_date = models.DateField(null=True, blank=True)
    swap_reason = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional information
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, related_name='bookings_created')
    
    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date must be before end date')
            
        # Check car availability
        if self.car and not self.id:  # Only check on new bookings
            overlapping_bookings = Booking.objects.filter(
                car=self.car,
                booking_status__in=['Active', 'Reserved'],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            
            if overlapping_bookings.exists():
                raise ValidationError('This car is already booked for the selected dates')
    
    def save(self, *args, **kwargs):
        # Generate booking ID on creation
        if not self.booking_id:
            unique_id = str(uuid.uuid4()).split('-')[0]
            self.booking_id = f"BK-{timezone.now().strftime('%Y%m%d')}-{unique_id}"
        
        # Calculate subtotal and total
        if not self.id:  # For new bookings
            delta = (self.end_date - self.start_date).days
            self.subtotal = self.car.fee * delta
            self.total_amount = self.subtotal + self.tax - self.discount
        
        self.clean()
        super().save(*args, **kwargs)
        
    def extend(self, new_end_date, extension_fee=0, reason=None, remarks=None, user=None):
        """
        Extend this booking to a new end date.
        - Creates a BookingExtension record.
        - Updates the booking's end_date and extension_charges.
        """
        if new_end_date <= self.end_date:
            raise ValidationError("New end date must be after current end date.")

        BookingExtension.objects.create(
            booking=self,
            previous_end_date=self.end_date,
            new_end_date=new_end_date,
            extension_fee=extension_fee,
            reason=reason,
            remarks=remarks,
            created_by=user
        )
        self.extension_charges += extension_fee
        self.end_date = new_end_date
        self.total_amount += extension_fee
        self.save(update_fields=['extension_charges', 'end_date', 'total_amount'])
            
    def swap_car(self, new_car, reason):
        """Swap the car assigned to this booking"""
        if self.has_been_swapped:
            old_car = self.original_car
        else:
            old_car = self.car
            self.original_car = old_car
            
        self.car = new_car
        self.has_been_swapped = True
        self.swap_date = timezone.now().date()
        self.swap_reason = reason
        self.save()
        
        # Update car statuses
        old_car.availability = 'Available'
        old_car.status = 'Active'
        old_car.save()
        
        new_car.availability = 'Booked'
        new_car.status = 'Booked'
        new_car.save()
    
    def get_duration_days(self):
        """Calculate the duration of booking in days."""
        return (self.end_date - self.start_date).days

    
    def __str__(self):
        return f"Booking {self.booking_id} - {self.customer.name} - {self.car.car_name}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Credit', 'Credit Card'),
        ('Debit', 'Debit Card'),
        ('Online', 'Online Transfer'),
    ]
    
    # Relationships
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    is_successful = models.BooleanField(default=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional information
    notes = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True, 
                             help_text="Additional comments about the payment")
    payment_method_details = models.TextField(blank=True, null=True, 
                                           help_text="Additional details about the payment method")
    receipt_image = models.ImageField(upload_to='payment_receipts/', blank=True, null=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                 null=True, related_name='payments_recorded')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update booking payment status
        booking = self.booking
        total_paid = Payment.objects.filter(booking=booking, is_successful=True).aggregate(
            total=models.Sum('amount'))['total'] or 0
        
        booking.paid_amount = total_paid
        
        if total_paid >= booking.total_amount:
            booking.payment_status = 'Paid'
        elif total_paid > 0:
            booking.payment_status = 'Partial'
        else:
            booking.payment_status = 'Unpaid'
            
        booking.save(update_fields=['paid_amount', 'payment_status'])
        
        # If this is the first payment, update payment date
        if not booking.payment_date:
            booking.payment_date = self.payment_date
            booking.save(update_fields=['payment_date'])
    
    def __str__(self):
        return f"Payment of ${self.amount} for {self.booking.booking_id}"
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['payment_method']),
        ]
        
 """ Booking Extension model for managing booking extensions.
    This model allows for the extension of existing bookings, including
    tracking the previous and new end dates, extension fees, and any
    additional remarks or reasons for the extension.
  """

class BookingExtension(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='extensions')
    previous_end_date = models.DateField(help_text="The end date before extension")
    new_end_date = models.DateField(help_text="The new end date after extension")
    extension_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking_extensions_created'
    )

    def clean(self):
        if self.new_end_date <= self.previous_end_date:
            raise ValidationError("New end date must be after previous end date.")

    def __str__(self):
        return f"Extension for {self.booking.booking_id}: {self.previous_end_date} → {self.new_end_date}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'new_end_date']),
        ]
