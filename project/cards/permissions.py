from rest_framework import permissions

class IsAdminOrCreateOnly(permissions.BasePermission):
    """
    Allow anyone authenticated to GET or POST.
    Allow only admin to PUT, PATCH, DELETE.
    """
    def has_permission(self, request ,view):
        if request.method in ['GET', 'POST']:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff
