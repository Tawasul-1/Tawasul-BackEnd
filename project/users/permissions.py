from rest_framework.permissions import BasePermission
class IsFreeTrialValid(BasePermission):
    message = "your free trial has expired, please upgrade to premium"

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.is_premium