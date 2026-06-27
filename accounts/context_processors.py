from .models import User


def user_role_flags(request):
    user = getattr(request, 'user', None)
    is_student = False
    is_instructor = False
    is_admin = False
    if user and user.is_authenticated:
        role = getattr(user, 'role', '')
        is_student = role == User.Role.STUDENT
        is_instructor = role == User.Role.INSTRUCTOR
        is_admin = role == User.Role.ADMIN
    return {
        'is_student': is_student,
        'is_instructor': is_instructor,
        'is_admin': is_admin,
    }
