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



def check(request):
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
        address = payload.get("address", "") 

        # 3) Validate action
        if action not in ("checkin", "checkout"):
            return HttpResponseBadRequest(
                json.dumps({"error": "Action must be 'checkin' or 'checkout'."}),
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

        # 8) Perform checkin / checkout logic
        if action == "checkin":
            if attendance_obj.checkin_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You have already checked in today."}),
                    content_type="application/json",
                )
            attendance_obj.checkin_time = timezone.now()
            attendance_obj.checkin_latitude = latitude
            attendance_obj.checkin_longitude = longitude
            attendance_obj.checkin_address = address


        else:  # action == "checkout"
            if not attendance_obj.checkin_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You must check in before clocking out."}),
                    content_type="application/json",
                )
            if attendance_obj.checkout_time:
                return HttpResponseBadRequest(
                    json.dumps({"error": "You have already checked out today."}),
                    content_type="application/json",
                )
            attendance_obj.checkout_time = timezone.now()
            attendance_obj.checkout_location_latitude = latitude
            attendance_obj.checkout_location_longitude = longitude
            attendance_obj.checkout_address = address

        attendance_obj.save()

        # 9) Manually build a JSON response (no DRF serializer)
        response_data = {
            "id": attendance_obj.id,
            "user": attendance_obj.user.id,
            "date": attendance_obj.date.isoformat(),
            "checkin_time": attendance_obj.checkin_time.isoformat() if attendance_obj.checkin_time else None,
            "checkout_time": attendance_obj.checkout_time.isoformat() if attendance_obj.checkout_time else None,
            "checkin_latitude": attendance_obj.checkin_latitude,
            "checkin_longitude": attendance_obj.checkin_longitude,
            "checkout_latitude": attendance_obj.checkout_latitude,
            "checkout_longitude": attendance_obj.checkout_longitude,
            "checkin_address": attendance_obj.checkin_address,
            "checkout_address": attendance_obj.checkout_address,

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

# def check(request):

#     return render(request, 'app/check.html')