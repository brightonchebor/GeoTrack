from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('attachee', 'Attachee'),
        ('supervisor', 'Supervisor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attachee')

class Attendance(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()

    checkin_time = models.DateTimeField(null=True, blank=True)  # Store clock-in time
    checkout_time = models.DateTimeField(null=True, blank=True)  # Store clock-out time

    checkin_latitude = models.FloatField(null=True, blank=True)  # Latitude for clock-in location
    checkin_longitude = models.FloatField(null=True, blank=True)  # Longitude for clock-in location

    checkout_latitude = models.FloatField(null=True, blank=True)  # Latitude for clock-out location
    checkout_longitude = models.FloatField(null=True, blank=True)  # Longitude for clock-out location

    checkin_address = models.TextField(null=True, blank=True)
    checkout_address = models.TextField(null=True, blank=True)
    
    def __str__(self):
        
        return f'{self.user.first_name}, {self.user.last_name} - {self.date}'
    
    class Meta:

        unique_together = ("user", "date")
        ordering = ["-date"]

class Geofence(models.Model):

    office_lat = models.FloatField()
    office_long = models.FloatField()
    geofence_radius = models.FloatField()

    def __str__(self):
        return f'latitude:{self.office_lat}, longitude:{self.office_long}, radius:{self.geofence_radius}'