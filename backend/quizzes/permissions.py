from rest_framework.permissions import BasePermission
# from accounts.permissions import IsAuthenticatedUser, IsManager


class CanCreateQuiz(BasePermission):

    def has_permission(self, request, view):

        user = request.user

        # Admin manager always allowed
        if user.is_authenticated and user.is_manager:
            return True

        # Teachers handled later
        return False

class CanEditQuiz(BasePermission):

    def has_object_permission(self, request, view, quiz):

        user = request.user

        # Manager overrides everything
        if user.is_manager:
            return True
        
        # Teacher only get's access only if there's no quiz attempts
        if user.is_teacher and not quiz.attempts.exists():
            return True

        # If quiz has attempts → locked for all non-managers admin
        if quiz.attempts.exists():
            return False

        return False

class CanManageQuestions(BasePermission):

    def has_object_permission(self, request, view, quiz):

        user = request.user

        # Manager overrides everything
        if user.is_manager:
            return True
        
        # Teacher only get's access only if there's no quiz attempts
        if user.is_teacher and not quiz.attempts.exists():
            return True

        # If quiz has attempts → locked for all non-managers admin
        if quiz.attempts.exists():
            return False

        return False
    
class CanAttemptQuiz(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_admin:
            return False

        return True

    # Build has object permission

 # 🔥 Manually trigger object-level permission check
# self.check_object_permissions(request, quiz)