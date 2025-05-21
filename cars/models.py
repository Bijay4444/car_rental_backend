from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class Car(models.Model):
    """
    Model representing a car in the rental system.

    Stores car details, specifications, insurance info, status, and audit fields.
    Supports soft deletion with reason tracking.

    Attributes:
        car_image (ImageField): Optional image of the car.
        car_name (str): Name of the car.
        fee (Decimal): Rental fee per day.
        tracker_expiry_date (date): Expiry date of the car's tracker.
        color (str): Car color.
        seats (int): Number of seats.
        mileage (str): Mileage information.
        type (str): Type of car (SUV, Sedan, etc.).
        gearbox (str): Gearbox type (Automatic/Manual).
        max_speed (str): Maximum speed.
        collision_damage_waiver (bool): Insurance option.
        third_party_liability_insurance (bool): Insurance option.
        optional_insurance_add_ons (bool): Insurance option.
        insurance_expiry_date (date): Insurance expiry date.
        status (str): Current status (Active, Booked, etc.).
        availability (str): Availability status.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        created_by (User): User who created the record.
        updated_by (User): User who last updated the record.
        is_deleted (bool): Soft delete flag.
        deleted_at (datetime): Deletion timestamp.
        deleted_by (User): User who deleted the record.
    """
    CAR_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('Sedan', 'Sedan'),
        ('Hatchback', 'Hatchback'),
        ('Van', 'Van'),
        ('Convertible', 'Convertible'),
        ('Sport Car', 'Sport Car'),
    ]
    GEARBOX_CHOICES = [
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Booked', 'Booked'),
        ('Returned', 'Returned'),
        ('Overdue', 'Overdue'),
    ]
    AVAILABILITY_CHOICES = [
        ('Available', 'Available'),
        ('Booked', 'Booked'),
        ('Reserved', 'Reserved'),
    ]

    # Basic Information
    car_image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    car_name = models.CharField(max_length=100, db_index=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, help_text="Fee per day")
    tracker_expiry_date = models.DateField()

    # Specification
    color = models.CharField(max_length=50)
    seats = models.PositiveIntegerField()
    mileage = models.CharField(max_length=20, help_text="e.g. 29 mpg")
    type = models.CharField(max_length=20, choices=CAR_TYPE_CHOICES, db_index=True)
    gearbox = models.CharField(max_length=10, choices=GEARBOX_CHOICES)
    max_speed = models.CharField(max_length=20)

    # Insurance Information
    collision_damage_waiver = models.BooleanField(default=False)
    third_party_liability_insurance = models.BooleanField(default=False)
    optional_insurance_add_ons = models.BooleanField(default=False)
    insurance_expiry_date = models.DateField()

    # Status/Availability
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', db_index=True)
    availability = models.CharField(max_length=10, choices=AVAILABILITY_CHOICES, default='Available', db_index=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cars_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cars_updated')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='cars_deleted')

    def clean(self):
        """
        Validate tracker and insurance expiry dates.

        Raises:
            ValidationError: If dates are in the past.
        """
        if self.tracker_expiry_date and self.tracker_expiry_date < timezone.now().date():
            raise ValidationError('Tracker expiry date must be in the future')
            
        if self.insurance_expiry_date and self.insurance_expiry_date < timezone.now().date():
            raise ValidationError('Insurance expiry date must be in the future')
    
    def soft_delete(self, user=None, reason=None, description=None):
        """
        Soft delete a car and record the reason.

        Args:
            user (User, optional): User performing the deletion.
            reason (str, optional): Reason for deletion.
            description (str, optional): Additional description.

        Returns:
            bool: True if deletion was successful.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
        
        # Create delete reason record
        if reason:
            CarDeleteReason.objects.create(
                car=self,
                reason=reason,
                description=description,
                deleted_by=user
            )
        return True
    
    def __str__(self):
        """
        Return the string representation of the car.

        Returns:
            str: Car name.
        """
        return self.car_name

    class Meta:
        ordering = ['car_name']
        indexes = [
            models.Index(fields=['status', 'availability']),
            models.Index(fields=['type']),
            models.Index(fields=['fee']),
        ]


class CarDeleteReason(models.Model):
    """
    Model to track reasons for car deletion.

    Attributes:
        car (Car): The car that was deleted.
        reason (str): Reason for deletion.
        description (str): Additional description.
        deleted_at (datetime): Deletion timestamp.
        deleted_by (User): User who deleted the car.
    """
    
    REASON_CHOICES = [
        ('Accident', 'Accident'),
        ('Maintenance', 'Maintenance'),
        ('Expired Insurance', 'Expired Insurance'),
        ('Others', 'Others'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='delete_reasons')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        """
        Return a string describing the deletion reason.

        Returns:
            str: Description of the deletion reason.
        """
        return f"{self.car.car_name} deleted due to {self.get_reason_display()}"
    
    class Meta:
        ordering = ['-deleted_at']
