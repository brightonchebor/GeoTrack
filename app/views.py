import json
from datetime import date as date_cls
from django.shortcuts import render
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from geopy.distance import great_circle
from .models import Attendance, Geofence


@login_required
def attendance_check(request):
    """
    GET:  Render the 'check.html' template, passing in today's Attendance (if any).
    POST: Accept JSON { action, latitude, longitude } via AJAX,
          perform geofence check, create/update Attendance, and return JSON.
    """

    user = request.user

    if request.method == "GET":
        # 1) Look up today's Attendance (if it exists) so the template can show Clock-In/Out times.
        today = date_cls.today()
        attendance = Attendance.objects.filter(user=user, date=today).first()

        context = {
            "today_attendance": attendance,
            "user": user,
        }
        return render(request, "app/check.html", context)

    elif request.method == "POST":
        # 2) Parse JSON body from fetch(...) in the template
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest(
                json.dumps({"error": "Invalid JSON payload."}),
                content_type="application/json",
            )

        action = payload.get("action")
        latitude = payload.get("latitude")
        longitude = payload.get("longitude")

        # 3) Validate action
        if action not in ("clock_in", "clock_out"):
            return HttpResponseBadRequest(
                json.dumps({"error": "Action must be 'clock_in' or 'clock_out'."}),
                content_type="application/json",
            )

        # 4) Validate latitude/longitude presence and numeric
        if latitude is None or longitude is None:
            return HttpResponseBadRequest(
                json.dumps({"error": "Latitude and longitude are required."}),
                content_type="application/json",
            )
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return HttpResponseBadRequest(
                json.dumps({"error": "Latitude and longitude must be valid numbers."}),
                content_type="application/json",
            )

        # 5) Load (the first) Geofence row
        geofence = Geofence.objects.first()
        if not geofence:
            return HttpResponseBadRequest(
                json.dumps({"error": "No geofence configured on the server."}),
                content_type="application/json",
            )

        office_lat = geofence.office_lat
        office_long = geofence.office_long
        geofence_radius = geofence.geofence_radius  # in meters

        # 6) Check distance
        distance_m = great_circle((office_lat, office_long), (latitude, longitude)).meters
        if distance_m > geofence_radius:
            return HttpResponseForbidden(
                json.dumps({"error": "Location is outside the allowed geofence."}),
                content_type="application/json",
            )

        # 7) Get or create today's Attendance record
        today = date_cls.today()
        attendance_obj, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
        )

        # 8) Perform clock_in / clock_out logic
        if action == "clock_in":
            if attendance_obj.clock_in_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You have already clocked in today."}),
                    content_type="application/json",
                )
            attendance_obj.clock_in_time = timezone.now()
            attendance_obj.clock_in_location_latitude = latitude
            attendance_obj.clock_in_location_longitude = longitude

        else:  # action == "clock_out"
            if not attendance_obj.clock_in_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You must clock in before clocking out."}),
                    content_type="application/json",
                )
            if attendance_obj.clock_out_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You have already clocked out today."}),
                    content_type="application/json",
                )
            attendance_obj.clock_out_time = timezone.now()
            attendance_obj.clock_out_location_latitude = latitude
            attendance_obj.clock_out_location_longitude = longitude

        attendance_obj.save()

        # 9) Manually build a JSON response (no DRF serializer)
        response_data = {
            "id": attendance_obj.id,
            "user": attendance_obj.user.id,
            "date": attendance_obj.date.isoformat(),
            "clock_in_time": attendance_obj.clock_in_time.isoformat() if attendance_obj.clock_in_time else None,
            "clock_out_time": attendance_obj.clock_out_time.isoformat() if attendance_obj.clock_out_time else None,
            "clock_in_location_latitude": attendance_obj.clock_in_location_latitude,
            "clock_in_location_longitude": attendance_obj.clock_in_location_longitude,
            "clock_out_location_latitude": attendance_obj.clock_out_location_latitude,
            "clock_out_location_longitude": attendance_obj.clock_out_location_longitude,
        }

        # HTTP 200 if just created; 202 if updating an existing record
        status_code = 200 if created else 202
        return JsonResponse(response_data, status=status_code)

    else:
        return HttpResponseBadRequest(
            json.dumps({"error": "Unsupported HTTP method."}),
            content_type="application/json",
        )

def home(request):

    return render(request, 'app/home.html')

def check(request):

    return render(request, 'app/check.html')