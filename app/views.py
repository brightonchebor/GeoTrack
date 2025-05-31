from django.shortcuts import render

# Create your views here.
def home(request):

    return render(request, 'app/home.html')

def check(request):

    return render(render, 'app/check.html')

def login_view(request):

    return render(request, 'app/login.hmtl')

def register(request):

    return render(request, 'app/register.hmtl')

def logout_view(request):

    return render(request, 'app/logout.hmtl')