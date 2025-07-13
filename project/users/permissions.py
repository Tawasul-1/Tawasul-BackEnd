from rest_framework.permissions import BasePermission
class IsFreeTrialValid(BasePermission):
    message = "your free trial has expired, please upgrade to premium"

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.is_premium
    
class IsPremiumUser(BasePermission):
    message = " this content is only available for premium users."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_premium