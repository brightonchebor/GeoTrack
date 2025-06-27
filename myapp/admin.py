from django.contrib import admin
from .models import CustomUser, Attendance, Geofence

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Admin settings for CustomUser model.
    """
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'user_type',           # raw value
        'get_user_type_display',  # human‐readable
        'is_staff',
        'is_active',
    )
    list_filter = (
        'user_type',
        'is_staff',
        'is_active',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    ordering = ('username',)

    # If you don’t want both the raw and the display value in the list, you can
    # drop one of them. You can also rename the column header for get_user_type_display:
    get_user_type_display.short_description = 'Role'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Admin settings for Attendance model.
    """
    list_display = ('user', 'date', 'checkin_time', 'checkout_time')
    list_filter  = ('date',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    """
    Admin settings for Geofence model.
    """
    list_display = ('office_lat', 'office_long', 'geofence_radius')
