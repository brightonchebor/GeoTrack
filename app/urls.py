from django.urls import path
from .views import *

app_name = 'app'

urlpatterns = [
    path('', home, name='home'),
    path('check/', check, name='check'),
    path('login/', logout_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
]
