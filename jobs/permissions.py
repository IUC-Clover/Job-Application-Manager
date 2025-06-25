from rest_framework import permissions

class IsJobSeeker(permissions.BasePermission):
    """
    Custom permission to only allow job seekers to perform an action.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'job_seeker'

class IsEmployerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow employers to create objects.
    Read-only for others.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'employer'

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.employer == request.user 