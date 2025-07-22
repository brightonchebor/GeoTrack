from django.urls import path
from .views import *


app_name = 'myapp'

urlpatterns = [
   path('', home, name='home'),

   path('users/register/', register, name='register'),
   path('users/verify-email/', verify_email, name='otp'),
   path('users/login/', login_view, name='login'),
   path('users/logout/', logout_view, name='logout'),

   path('users/attendance/', attendance, name='attendance'),

   path('dashboard/staff/', StaffDashboardView.as_view(), name='staff_dashboard'),
   path('dashboard/member/', MemberDashboardView.as_view(), name='member_dashboard'),
   path('member-attendance/<int:member_id>/', MemberAttendanceDetailView.as_view(), name='member_attendance_detail'),
   path('export-member-attendance/<int:member_id>/', export_member_attendance_csv, name='export_member_attendance'),
   path('export-all-attendance/', export_all_attendance_csv, name='export_all_attendance'),

]

