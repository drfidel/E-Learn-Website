from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'role', 'is_instructor_approved', 'is_staff')
    fieldsets = UserAdmin.fieldsets + ((
        'Additional Info',
        {
            'fields': ('role', 'photo', 'bio', 'qualifications', 'is_instructor_approved'),
        },
    ),)
    add_fieldsets = UserAdmin.add_fieldsets + ((
        'Additional Info',
        {
            'fields': ('email', 'role'),
        },
    ),)
