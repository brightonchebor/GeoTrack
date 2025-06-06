from django.contrib import admin
from .models import Attendance, Geofence


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'checkin_time', 'checkout_time',
        'checkin_latitude', 'checkin_longitude',
        'checkout_latitude', 'checkout_longitude'
    )
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-date',)
    readonly_fields = ('checkin_time', 'checkout_time')

@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ('office_lat', 'office_long', 'geofence_radius')
    search_fields = ('office_lat', 'office_long')
