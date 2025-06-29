from django.urls import path
from .views import *
from .views import *

app_name = 'myapp'

urlpatterns = [
   path('', home, name='home'),

   path('register/', register, name='register'),
   path('login/', login_view, name='login'),
   path('logout/', logout_view, name='logout'),

   path('attendance/', attendance, name='attendance'),

   path('dashboard/staff/', StaffDashboardView.as_view(), name='staff_dashboard'),
   path('dashboard/member/', MemberDashboardView.as_view(), name='member_dashboard')
]

