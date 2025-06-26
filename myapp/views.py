from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from app.models import UserProfile

def home(request):
   return render(request, 'myapp/home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '')

        # Validate required fields
        if not all([username, password, confirm_password, email, role]):
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
                email=email
            )

            # Create user profile
            UserProfile.objects.create(user=user, role=role)

            messages.success(request, 'Your profile has been set up! Login and explore your dashboard.')
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
            messages.success(request, 'You are now logged in')
            return redirect('myapp:home')
        else:
            messages.error(request, 'Invalid login credentials')
            return render(request, 'myapp/login.html')

    # GET request - show login form
    return render(request, 'myapp/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('myapp:home')

