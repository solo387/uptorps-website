from rest_framework.permissions import BasePermission

# Base permission
class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
# Primary role permissions
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == request.user.Role.STUDENT
        )


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == request.user.Role.TEACHER
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin

# Admin subtype permissions
class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_manager
        )
class IsAdminManager(BasePermission):
    """
    Only admin with MANAGER type
    """

    def has_permission(self, request, view):
        # user = request.user

        return (
            IsAuthenticatedUser.has_permission(request, view)
            and IsAdmin.has_permission(request, view)
            and IsManager.has_permission(request, view)
        )

class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_developer
        )

# Developers specialization permissions
class IsFrontendDev(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_developer
            and request.user.dev_specialization == request.user.DevSpecialization.FRONTEND
        )


class IsBackendDev(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_backend_dev
        )


class IsSecurityDev(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_security_dev
        )


# Object level permission
class IsSelfOrAdmin(BasePermission):
    """
    Allows access only to the object owner or an admin user.
    """

    def has_object_permission(self, request, view, obj):
        # Admins can access any object
        if request.user.is_admin:
            return True

        # Object owner access (UUID match)
        return str(obj.uuid) == str(request.user.uuid)