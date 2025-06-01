from django.shortcuts import render

# Create your views here.
def home(request):

    return render(request, 'app/home.html')

def check(request):

    return render(request, 'app/check.html')

