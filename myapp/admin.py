from django.contrib import admin
from .models import CustomUser, Attendance, Geofence, OneTimePassword

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    
    list_display = (
        'email',
        'first_name',
        'last_name',        # ← our custom column
        'is_verified',
        'department',
        'user_type',
    )
    list_filter = (
        'is_staff',
        'is_active',
    )

admin.site.register(OneTimePassword)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    
    list_display   = ('user', 'date', 'checkin_time', 'checkout_time')
    list_filter    = ('date',)
    search_fields  = ('user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date'


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    
    list_display = ('office_lat', 'office_long', 'geofence_radius', 'office_name')
