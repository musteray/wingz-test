from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

USER_ROLES = [
    ('driver', 'Driver'),
    ('driver', 'Admin'),
]
RIDE_STATUSES = [
    ('en-route', 'En Route'),
    ('pickup', 'Pick Up'),
    ('dropoff', 'Dropoff')
]

class User(AbstractUser):
    """User model matching the specified schema"""
    id_user = models.BigAutoField(primary_key=True, verbose_name='ID')
    role = models.CharField(max_length=50, choices=USER_ROLES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.role})"


class Ride(models.Model):
    """Ride model matching the specified schema"""
    id_ride = models.BigAutoField(primary_key=True, verbose_name='ID')
    status = models.CharField(max_length=50, choices=RIDE_STATUSES)
    id_rider = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='rides_as_rider',
        db_column='id_rider'
    )
    id_driver = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rides_as_driver',
        db_column='id_driver'
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()
    
    class Meta:
        db_table = 'ride'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['pickup_time']),
            models.Index(fields=['id_rider']),
            models.Index(fields=['id_driver']),
            # Composite index for efficient filtering
            models.Index(fields=['status', 'pickup_time']),
            # Indexes for pickup coordinates (for distance sorting)
            models.Index(fields=['pickup_latitude', 'pickup_longitude']),
        ]
    
    def __str__(self):
        return f"Ride #{self.id_ride} - {self.status}"


class RideEvent(models.Model):
    """RideEvent model matching the specified schema"""
    id_ride_event = models.BigAutoField(primary_key=True, verbose_name='ID')
    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='events',
        db_column='id_ride'
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    
    class Meta:
        db_table = 'ride_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id_ride', 'created_at']),
            # Critical index for efficient filtering of today's events
            models.Index(fields=['id_ride', '-created_at']),
        ]
    
    def __str__(self):
        return f"Event #{self.id_ride_event} - Ride #{self.id_ride_id}"