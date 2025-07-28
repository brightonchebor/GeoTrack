from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.conf import settings 
from django.utils.translation import gettext_lazy as _
from .managers import UserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    
    CHOICES = (
        ("staff", "Staff"),
        ("member", "Member"),
    )

    DEPARTMENT_CHOICES = (
        ('', '-- Select Department --'),
        ('communication', 'Communication'),
        ('creatives', 'Creatives'),
        ('tech_department', 'Tech Department'),
        ('community_experience', 'Community Experience'),
        ('youth_engagement', 'Youth Engagement'),
        ('heritage', 'Heritage'),
        ('admin', 'Admin'),
        ('finance', 'Finance'),
        ('entrepreneurship', 'Entrepreneurship'),
    )

    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=15 ,choices=CHOICES, default='member', db_index=True)
    department = models.CharField(max_length=25, choices=DEPARTMENT_CHOICES, null=True, blank=True)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"    

class OneTimePassword(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)

    def __srt__(self):
        return f'{self.user.first_name}-passcode'

class Attendance(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
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
    office_name = models.TextField()

    def __str__(self):
        return f'latitude:{self.office_lat}, longitude:{self.office_long}, radius:{self.geofence_radius}'

