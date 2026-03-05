from rest_framework.permissions import BasePermission


class IsSuperadmin(BasePermission):
    """
    Only superadmin can access
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'superadmin'
        )


class IsAdmin(BasePermission):
    """
    Only admin can access (not superadmin)
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'admin'
            and request.user.is_account_active  # Check if plan is active
        )


class IsUser(BasePermission):
    """
    Only user can access
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'user'
        )
        
class IsAuthenticatedUser(BasePermission):
    message = "Access denied. Active user account required."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != 'user':
            return False
        return request.user.is_account_active        