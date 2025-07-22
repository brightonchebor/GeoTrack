from django.shortcuts import render, redirect
from datetime import date as date_cls
from .models import CustomUser as User, OneTimePassword
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
from .utils import send_code_to_user
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from datetime import timedelta
import csv



def home(request):
   return render(request, 'myapp/home.html')

def register(request):
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        email = request.POST.get('email', '').strip()

        if not all([first_name, last_name, password, confirm_password, email]):
            messages.error(request, 'All fields are required.')
            return redirect('myapp:register')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return redirect('myapp:register')

        if password != confirm_password:
            messages.error(request, 'Password mismatch. Ensure both fields are identical')
            return redirect('myapp:register')

        try:

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
                return redirect('myapp:register')

            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                password=password,
                email=email
            )
            send_code_to_user(user.email)
            messages.success(request, 'Account created successfully! Please check your email for verification code.')
            return redirect('myapp:otp')

        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('myapp:register')

    return render(request, 'myapp/signup.html')

def verify_email(request):

    if request.method == 'POST':
        otpcode = request.POST.get('otp', '').strip()

        if not otpcode:
            messages.error(request, 'Please enter the verification code.')
            return redirect('myapp:otp')

        try:
            otp_obj = OneTimePassword.objects.get(code=otpcode)
            user = otp_obj.user

            if user.is_verified:
                messages.info(request, 'Your account is already verified.')
                return redirect('myapp:login')

            user.is_verified = True
            user.save()

            messages.success(request, 'Account verified successfully!')
            return redirect('myapp:login')

        except OneTimePassword.DoesNotExist:
            messages.error(request, 'Invalid verification code.')
            return redirect('myapp:otp')

    return render(request, 'myapp/otp.html')

def login_view(request):
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'myapp/login.html')

        user = authenticate(request, email=email, password=password)

        # 1) Authentication failed?
        if user is None:
            messages.error(request, 'Invalid login credentials.')
            return render(request, 'myapp/login.html')

        # 2) Not yet verified?
        if not user.is_verified:
            messages.error(request, 'Please check your email for a verification code before logging in.')
            return render(request, 'myapp/login.html')

        # 3) OK!  Log them in and redirect based on user_type
        login(request, user)
        #messages.success(request, 'You are now logged in.')  # optional

        if user.user_type == 'member':
            return redirect('myapp:attendance')
        else:
            return redirect('myapp:staff_dashboard')

    # GET (or any non-POST) just renders the form
    return render(request, 'myapp/login.html')

def logout_view(request):
    logout(request)
    # messages.success(request, 'You have been logged out successfully.')
    return redirect('myapp:home')

@login_required
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

@login_required
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

@login_required
class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "myapp/staff_dashboard.html"

    def test_func(self):
        # Only allow users marked as staff to view this
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        current_staff = self.request.user

        # 1. Filter members by department - only show members from the same department as the staff
        if current_staff.department:
            members = CustomUser.objects.filter(user_type="member", department=current_staff.department)
        else:
            # If staff has no department assigned, show all members (fallback)
            members = CustomUser.objects.filter(user_type="member")
        
        ctx["members"] = members

        # 2. Today's attendance - only for members in the same department
        member_ids = list(members.values_list('id', flat=True))
        today_attendance = Attendance.objects.filter(date=today, user_id__in=member_ids)
        ctx["today_attendance"] = today_attendance

        # 3. Create a dictionary to map user_id to attendance record for efficient lookup
        attendance_by_user = {}
        for attendance in today_attendance:
            attendance_by_user[attendance.user.id] = attendance

        ctx["attendance_by_user"] = attendance_by_user

        # 4. Create a set of user IDs who are present today for easy lookup
        present_user_ids = set(today_attendance.values_list('user_id', flat=True))
        ctx["present_user_ids"] = present_user_ids

        # 5. Calculate counts for dashboard cards - based on department members only
        total_members = members.count()
        present_count = len(present_user_ids)
        absent_count = total_members - present_count
        
        ctx["absent_count"] = absent_count

        # 6. Monthly summary: how many days each member has checked in - department filtered
        first_of_month = today.replace(day=1)
        summary = (
            Attendance.objects
            .filter(date__gte=first_of_month, date__lte=today, user_id__in=member_ids)
            .values("user__id", "user__first_name", "user__last_name")
            .annotate(days_checked_in=models.Count("id"))
            .order_by("-days_checked_in")
        )
        ctx["monthly_summary"] = summary

        # 7. (Optional) The defined geofence
        ctx["geofence"] = None
        from .models import Geofence
        try:
            ctx["geofence"] = Geofence.objects.first()
        except Geofence.DoesNotExist:
            pass

        # 8. Add department info to context for display
        ctx["staff_department"] = current_staff.department
        ctx["department_display"] = dict(CustomUser.DEPARTMENT_CHOICES).get(current_staff.department, 'No Department')

        return ctx

@login_required
def export_all_attendance_csv(request):
    """Export attendance data for members in the same department as the staff user"""
    if not request.user.is_staff:
        return HttpResponseForbidden("Access denied")
    
    current_staff = request.user
    
    # Filter members by department
    if current_staff.department:
        members = CustomUser.objects.filter(user_type='member', department=current_staff.department)
        filename_suffix = f"_{current_staff.department}_department"
    else:
        # Fallback: show all members if staff has no department
        members = CustomUser.objects.filter(user_type='member')
        filename_suffix = "_all_departments"
    
    # Get attendance for filtered members only
    member_ids = list(members.values_list('id', flat=True))
    all_attendance = Attendance.objects.filter(user_id__in=member_ids).select_related('user').order_by('-date', 'user__first_name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="members_attendance{filename_suffix}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'First Name', 'Last Name', 'Email', 'Department', 'Date', 'Day of Week', 
        'Check In Time', 'Check Out Time', 'Total Hours', 'Status',
    ])
    
    for record in all_attendance:
        # Calculate total hours
        total_hours = ''
        if record.checkin_time and record.checkout_time:
            time_diff = record.checkout_time - record.checkin_time
            total_hours = round(time_diff.total_seconds() / 3600, 2)
        
        # Determine status
        if not record.checkin_time:
            status = 'No Show'
        elif record.checkin_time and not record.checkout_time:
            status = 'In Progress'
        else:
            status = 'Full Day'
        
        # Get department display name
        department_display = dict(CustomUser.DEPARTMENT_CHOICES).get(record.user.department, 'No Department')
        
        writer.writerow([
            record.user.first_name,
            record.user.last_name,
            record.user.email,
            department_display,
            record.date.strftime('%Y-%m-%d'),
            record.date.strftime('%A'),
            record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else '',
            record.checkout_time.strftime('%H:%M:%S') if record.checkout_time else '',
            total_hours,
            status,
        ])
    
    return response

@login_required
class MemberAttendanceDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "myapp/member_attendance_detail.html"

    def test_func(self):
        # Only allow staff to view this
        return self.request.user.is_staff

    def get_object(self):
        """Get the member, ensuring they're in the same department as the staff user"""
        member_id = self.kwargs.get('member_id')
        current_staff = self.request.user
        
        # Filter by department if staff has a department assigned
        if current_staff.department:
            member = get_object_or_404(
                CustomUser, 
                id=member_id, 
                user_type='member',
                department=current_staff.department
            )
        else:
            # Fallback: allow access to any member if staff has no department
            member = get_object_or_404(CustomUser, id=member_id, user_type='member')
        
        return member

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        member = self.get_object()
        
        # Get all attendance records for this member
        attendance_records = Attendance.objects.filter(user=member).order_by('-date')
        
        # Calculate additional data for each record
        records_with_hours = []
        total_hours = 0
        full_days = 0
        partial_days = 0
        
        for record in attendance_records:
            record_data = record
            if record.checkin_time and record.checkout_time:
                # Calculate total hours worked
                time_diff = record.checkout_time - record.checkin_time
                hours = time_diff.total_seconds() / 3600
                record_data.total_hours = hours
                total_hours += hours
                full_days += 1
            elif record.checkin_time:
                record_data.total_hours = None
                partial_days += 1
            else:
                record_data.total_hours = None
                
            records_with_hours.append(record_data)
        
        ctx.update({
            'member': member,
            'attendance_records': records_with_hours,
            'total_days': attendance_records.count(),
            'full_days': full_days,
            'partial_days': partial_days,
            'total_hours': total_hours,
        })
        
        return ctx

@login_required
def export_member_attendance_csv(request, member_id):
    """Export a specific member's attendance data as CSV (with department check)"""
    if not request.user.is_staff:
        return HttpResponseForbidden("Access denied")
    
    current_staff = request.user
    
    # Filter by department if staff has a department assigned
    if current_staff.department:
        member = get_object_or_404(
            CustomUser, 
            id=member_id, 
            user_type='member',
            department=current_staff.department
        )
    else:
        # Fallback: allow access to any member if staff has no department
        member = get_object_or_404(CustomUser, id=member_id, user_type='member')
    
    attendance_records = Attendance.objects.filter(user=member).order_by('-date')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{member.first_name}_{member.last_name}_attendance.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Day of Week', 'Check In Time', 'Check Out Time', 
        'Total Hours', 'Status', 'Department'
    ])
    
    department_display = dict(CustomUser.DEPARTMENT_CHOICES).get(member.department, 'No Department')
    
    for record in attendance_records:
        # Calculate total hours
        total_hours = ''
        if record.checkin_time and record.checkout_time:
            time_diff = record.checkout_time - record.checkin_time
            total_hours = round(time_diff.total_seconds() / 3600, 2)
        
        # Determine status
        if not record.checkin_time:
            status = 'No Show'
        elif record.checkin_time and not record.checkout_time:
            status = 'In Progress'
        else:
            status = 'Full Day'
        
        writer.writerow([
            record.date.strftime('%Y-%m-%d'),
            record.date.strftime('%A'),
            record.checkin_time.strftime('%H:%M:%S') if record.checkin_time else '',
            record.checkout_time.strftime('%H:%M:%S') if record.checkout_time else '',
            total_hours,
            status,
            department_display,
        ])
    
    return response