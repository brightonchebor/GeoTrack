from django.contrib import admin
from django.contrib.auth.models import User
from .models import UserProfile, Attendance, Geofence

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin settings for UserProfile model.
    """
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Admin settings for Attendance model.
    """
    list_display = ('user', 'date', 'checkin_time', 'checkout_time')
    list_filter = ('date',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'

@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    """
    Admin settings for Geofence model.
    """
    list_display = ('office_lat', 'office_long', 'geofence_radius')
