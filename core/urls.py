
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('', include('app.urls')),
    # path('', include('users.urls')),
    # path('', include('accounts.urls')),
    path('new/', include('myapp.urls')),
]
