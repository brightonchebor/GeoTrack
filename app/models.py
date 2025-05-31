from django.db import models
from auth.models import User

class Attendance(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    clock_in_time = models.DateTimeField(null=True, blank=True)  # Store clock-in time
    clock_out_time = models.DateTimeField(null=True, blank=True)  # Store clock-out time
    clock_in_location_latitude = models.FloatField(null=True, blank=True)  # Latitude for clock-in location
    clock_in_location_longitude = models.FloatField(null=True, blank=True)  # Longitude for clock-in location
    clock_out_location_latitude = models.FloatField(null=True, blank=True)  # Latitude for clock-out location
    clock_out_location_longitude = models.FloatField(null=True, blank=True)  # Longitude for clock-out location

    def __str__(self):
        return f'{self.user.first_name}, {self.user.last_name} - {self.date}'
    
    class Meta:
        unique_together = ('user', 'date')

class Geofence(models.Model):

    office_lat = models.FloatField()
    office_long = models.FloatField()
    geofence_radius = models.FloatField()

    def __str__(self):
        return f'latitude:{self.office_lat}, longitude:{self.office_long}, radius:{self.geofence_radius}'