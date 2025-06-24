from django.urls import path
from .views import *



urlpatterns = [
    path('accounts/login/', login_view, name='login_user'),
    path('accounts/register/', register, name='register_user'),
    path('accounts/logout/', logout_view, name='logout_user'),
]
