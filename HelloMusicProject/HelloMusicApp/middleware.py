from django.shortcuts import redirect
from django.http import HttpResponseRedirect

class LoginRequiredMiddleware:
    """Custom middleware to show a message when redirecting unauthenticated users to login"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is not authenticated and is not already on the login page
        if not request.user.is_authenticated and request.path not in ['/login/', '/register/', '/request-password-reset/'] and not request.path.startswith('/verify-reset/'):
            # Redirect to the login page
            return HttpResponseRedirect('/login/')
        
        # Continue processing the request as usual
        response = self.get_response(request)
        return response