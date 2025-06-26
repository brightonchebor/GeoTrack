from django.urls import path
from .views import *
from .views import *

app_name = 'myapp'

urlpatterns = [
   path('', home, name='home'),
   path('register/', register, name='register'),
   path('login/', login_view, name='login'),
   path('logout/', logout_view, name='logout'),
   path('attendance/', attendance, name='attendance')
]

