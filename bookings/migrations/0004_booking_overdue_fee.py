# Generated by Django 5.2 on 2025-05-26 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0003_alter_booking_dropoff_time_alter_booking_pickup_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='overdue_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
