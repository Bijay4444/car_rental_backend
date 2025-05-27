from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid

class Booking(models.Model):
    """
    Model representing a car booking.

    Stores booking details, customer, car, dates, payment, accident info, swap history, and audit fields.

    Attributes:
        booking_id (str): Unique booking identifier.
        customer (Customer): The customer who made the booking.
        car (Car): The car assigned to the booking.
        start_date (date): Booking start date.
        end_date (date): Booking end date.
        pickup_time (time): Scheduled pickup time.
        dropoff_time (time): Scheduled dropoff time.
        actual_return_date (date): Actual return date.
        booking_status (str): Status (Active, Returned, Cancelled, Overdue).
        car_returned (bool): Whether the car has been returned.
        payment_status (str): Payment status (Paid, Partial, Unpaid).
        subtotal (Decimal): Base fee * number of days.
        tax (Decimal): Tax amount.
        discount (Decimal): Discount amount.
        extension_charges (Decimal): Additional charges for extensions.
        total_amount (Decimal): Total amount due.
        paid_amount (Decimal): Amount paid.
        payment_date (date): Date of payment.
        payment_method (str): Payment method.
        has_accident (bool): Whether an accident occurred.
        accident_description (str): Description of accident.
        accident_date (date): Date of accident.
        accident_charges (Decimal): Charges due to accident.
        original_car (Car): Original car if swapped.
        has_been_swapped (bool): Whether car was swapped.
        swap_date (date): Date of car swap.
        swap_reason (str): Reason for car swap.
        remarks (str): Additional remarks.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        created_by (User): User who created the booking.
    """
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
    car = models.ForeignKey('cars.Car', on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    
    # Dates and times
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    pickup_time = models.TimeField(null=True, blank=True)
    dropoff_time = models.TimeField(null=True, blank=True)  

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
        """
        Validate booking dates and car availability.

        Raises:
            ValidationError: If dates are invalid or car is double-booked.
        """
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
        """
        Save the booking instance.

        - Generates a unique booking ID if not set.
        - Validates booking before saving.
        """
        # Generate booking ID on creation
        if not self.booking_id:
            unique_id = str(uuid.uuid4()).split('-')[0]
            self.booking_id = f"BK-{timezone.now().strftime('%Y%m%d')}-{unique_id}"
        
        self.clean()
        super().save(*args, **kwargs)

        
    def extend(self, new_end_date, extension_fee=0, reason=None, remarks=None, user=None):
        """
        Extend this booking to a new end date.

        Creates a BookingExtension record and updates booking's end_date and charges.

        Args:
            new_end_date (date): The new end date.
            extension_fee (Decimal): Additional fee for extension.
            reason (str, optional): Reason for extension.
            remarks (str, optional): Additional remarks.
            user (User, optional): User performing the extension.
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
        """
        Swap the car assigned to this booking.

        Args:
            new_car (Car): The replacement car.
            reason (str): Reason for swapping.
        """
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
        """
        Calculate the duration of booking in days.

        Returns:
            int: Number of days.
        """
        return (self.end_date - self.start_date).days

    
    def __str__(self):
        """
        Return the string representation of the booking.

        Returns:
            str: Booking summary.
        """
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
    """
    Model representing a payment for a booking.

    Attributes:
        booking (Booking): The related booking.
        amount (Decimal): Payment amount.
        payment_date (date): Date of payment.
        payment_method (str): Payment method.
        is_successful (bool): Whether payment was successful.
        transaction_id (str): Transaction identifier.
        notes (str): Additional notes.
        remarks (str): Additional remarks.
        payment_method_details (str): Details about the payment method.
        receipt_image (ImageField): Optional receipt image.
        created_at (datetime): Creation timestamp.
        created_by (User): User who recorded the payment.
    """
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
        """
        Save the payment and update booking payment status.

        """
        super().save(*args, **kwargs)
        booking = self.booking
        
        # If this is the first payment, update payment date
        if not booking.payment_date:
            booking.payment_date = self.payment_date
            booking.save(update_fields=['payment_date'])
    
    def __str__(self):
        """
        Return the string representation of the payment.

        Returns:
            str: Payment summary.
        """
        return f"Payment of ${self.amount} for {self.booking.booking_id}"
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_date']),
            models.Index(fields=['payment_method']),
        ]
        
class BookingExtension(models.Model):
    """
    Model representing an extension to a booking.

    Attributes:
        booking (Booking): The related booking.
        previous_end_date (date): End date before extension.
        new_end_date (date): New end date after extension.
        extension_fee (Decimal): Fee for extension.
        reason (str): Reason for extension.
        remarks (str): Additional remarks.
        created_at (datetime): Creation timestamp.
        created_by (User): User who created the extension.
    """
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
        """
        Validate that the new end date is after the previous end date.

        Raises:
            ValidationError: If new end date is not after previous.
        """
        if self.new_end_date <= self.previous_end_date:
            raise ValidationError("New end date must be after previous end date.")

    def __str__(self):
        """
        Return the string representation of the booking extension.

        Returns:
            str: Extension summary.
        """
        return f"Extension for {self.booking.booking_id}: {self.previous_end_date} → {self.new_end_date}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', 'new_end_date']),
        ]
