from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the view
    """
    def has_permission(self, request, view):
        # Check if user is authenticated and has admin role or is superuser
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.is_staff or 
             request.user.role == 'Admin')
        )
