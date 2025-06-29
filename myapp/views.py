from django.shortcuts import render, redirect
from datetime import date as date_cls
from .models import CustomUser as User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import *
import json
from datetime import date as date_cls
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.utils import timezone
from geopy.distance import great_circle
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView





def home(request):
   return render(request, 'myapp/home.html')

def attendance(request):
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
        geofence = Geofence.objects.first()

        context = {
            "today_attendance": attendance,
            "user": user,
            'my_secret_token': settings.MY_SECRET_TOKEN,
            "office_lat": geofence.office_lat if geofence else None,
            "office_long": geofence.office_long if geofence else None,
            "geofence_radius": geofence.geofence_radius if geofence else None,
        }
        
        return render(request, "myapp/attendance.html", context)

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

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        email = request.POST.get('email', '').strip()
        user_type = request.POST.get('user_type', '')

        # Validate required fields
        if not all([username, password, confirm_password, email, user_type]):
            messages.error(request, 'All fields are required.')
            return redirect('myapp:register')

        # Check password match
        if password != confirm_password:
            messages.error(request, 'Password mismatch. Ensure both fields are identical')
            return redirect('myapp:register')

        try:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists. Please choose a different username.')
                return redirect('myapp:register')

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
                return redirect('myapp:register')

            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                user_type=user_type
            )

            # messages.success(request, 'Your profile has been set up! Login and explore your dashboard.')
            return redirect('myapp:login')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('myapp:register')

    return render(request, 'myapp/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Validate required fields
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'myapp/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # messages.success(request, 'You are now logged in')
            if user.user_type == 'member':
                return redirect('myapp:attendance')
            else:
                return redirect('myapp:staff_dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return render(request, 'myapp/login.html')

    # GET request - show login form
    return render(request, 'myapp/login.html')

def logout_view(request):
    logout(request)
    # messages.success(request, 'You have been logged out successfully.')
    return redirect('myapp:home')


class MemberDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "myapp/member_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # All attendance records for this member, most recent first
        ctx["attendance_records"] = Attendance.objects.filter(user=user).order_by("-date")
        # For example: count of total days checked in this month
        today = timezone.localdate()
        first_of_month = today.replace(day=1)
        ctx["current_month_count"] = Attendance.objects.filter(
            user=user,
            date__gte=first_of_month,
            date__lte=today
        ).count()
        return ctx


class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "myapp/staff_dashboard.html"

    def test_func(self):
        # Only allow users marked as staff to view this
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # 1. All members
        members = CustomUser.objects.filter(user_type="member")
        ctx["members"] = members

        # 2. Today's attendance for all members
        today_attendance = Attendance.objects.filter(date=today)
        ctx["today_attendance"] = today_attendance

        # 3. Create a set of user IDs who are present today for easy lookup
        present_user_ids = set(today_attendance.values_list('user_id', flat=True))
        ctx["present_user_ids"] = present_user_ids

        # 4. Monthly summary: how many days each member has checked in so far this month
        first_of_month = today.replace(day=1)
        summary = (
            Attendance.objects
            .filter(date__gte=first_of_month, date__lte=today)
            .values("user__id", "user__username", "user__first_name", "user__last_name")
            .annotate(days_checked_in=models.Count("id"))
            .order_by("-days_checked_in")
        )
        ctx["monthly_summary"] = summary

        # 5. (Optional) The defined geofence
        ctx["geofence"] = None
        from .models import Geofence
        try:
            ctx["geofence"] = Geofence.objects.first()
        except Geofence.DoesNotExist:
            pass

        return ctx