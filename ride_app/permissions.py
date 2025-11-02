
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow users with 'admin' role to access the API.
    """
    message = "You must have 'admin' role to access this resource."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role"""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'admin'
        )