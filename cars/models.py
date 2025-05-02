from django.db import models

class Car(models.Model):
    CAR_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('Sedan', 'Sedan'),
        ('Hatchback', 'Hatchback'),
        ('Van', 'Van'),
        ('Convertible', 'Convertible'),
        ('Sport Car', 'Sport Car'),
        # Add more as needed
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

    car_image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    car_name = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=8, decimal_places=2, help_text="Fee per day")
    tracker_expiry_date = models.DateField()

    # Specification
    color = models.CharField(max_length=50)
    seats = models.PositiveIntegerField()
    mileage = models.CharField(max_length=20, help_text="e.g. 29 mpg")
    type = models.CharField(max_length=20, choices=CAR_TYPE_CHOICES)
    gearbox = models.CharField(max_length=10, choices=GEARBOX_CHOICES)
    max_speed = models.CharField(max_length=20)

    # Insurance Information
    collision_damage_waiver = models.BooleanField(default=False)
    third_party_liability_insurance = models.BooleanField(default=False)
    optional_insurance_add_ons = models.BooleanField(default=False)
    insurance_expiry_date = models.DateField()

    # Status/Availability
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    availability = models.CharField(max_length=10, choices=AVAILABILITY_CHOICES, default='Available')

    def __str__(self):
        return self.car_name
