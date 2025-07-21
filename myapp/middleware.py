from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import reverse, NoReverseMatch
import time

class SessionExpiryMiddleware(MiddlewareMixin):
    """
    Middleware to handle session expiry gracefully by redirecting users
    to login page instead of showing errors
    """
    
    def process_request(self, request):
        # URLs that don't need authentication - based on your actual URLs
        public_urls = [
            '/',  # home
            '/users/register/',
            '/users/verify-email/', 
            '/users/login/',
            '/users/logout/',
            '/static/',
            '/admin/login/',
        ]
        
        # Skip processing for public URLs
        for url in public_urls:
            if request.path.startswith(url):
                return None
        
        # URLs that require authentication - based on your actual protected URLs
        protected_urls = [
            '/users/attendance/',
            '/dashboard/staff/',
            '/dashboard/member/',
            '/member-attendance/',
            '/export-member-attendance/',
            '/export-all-attendance/',
        ]
        
        # Check if current URL needs authentication
        needs_auth = any(request.path.startswith(url) for url in protected_urls)
        
        if needs_auth:
            # If user is not authenticated at all
            if not request.user.is_authenticated:
                # Handle AJAX requests (like your attendance POST)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Session expired. Please log in again.',
                        'redirect_to_login': True
                    }, status=401)
                
                # Regular request - redirect to login
                messages.warning(request, 'Please log in to access that page.')
                return redirect('myapp:login')
            
            # User is authenticated - check if session is still valid
            elif not self.is_session_valid(request):
                # Log out the user
                logout(request)
                
                # Handle AJAX requests
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Your session has expired. Please log in again.',
                        'redirect_to_login': True
                    }, status=401)
                
                # Regular request
                messages.warning(request, 'Your session has expired. Please log in again.')
                return redirect('myapp:login')
            
            # Additional check for staff-only pages
            elif request.path.startswith('/dashboard/staff/') and not request.user.is_staff:
                messages.error(request, 'Access denied. Staff privileges required.')
                # Redirect based on user type
                if request.user.user_type == 'member':
                    return redirect('myapp:member_dashboard')
                else:
                    return redirect('myapp:attendance')
        
        return None
    
    def is_session_valid(self, request):
        """Check if the current session is still valid"""
        try:
            # Check if session exists
            if not request.session.session_key:
                return False
            
            # Check if user object is still accessible
            if not hasattr(request.user, 'id'):
                return False
            
            # Check if user is still verified
            if hasattr(request.user, 'is_verified') and not request.user.is_verified:
                return False
            
            # Update last activity time
            request.session['last_activity'] = time.time()
            
            return True
            
        except Exception:
            return False
    
    def process_response(self, request, response):
        """Update session activity on each request"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.session['last_activity'] = time.time()
        return response