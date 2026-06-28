from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        'email',
        'username',
        'role',
        'is_instructor_approved',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = ('role', 'is_instructor_approved', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'headline', 'country', 'city')
    ordering = ('-date_joined',)
    list_per_page = 25
    fieldsets = UserAdmin.fieldsets + (
        (
            'Profile',
            {
                'fields': (
                    'role',
                    'photo',
                    'headline',
                    'bio',
                    'learning_goals',
                    'qualifications',
                    'is_instructor_approved',
                ),
            },
        ),
        (
            'Contact & Location',
            {
                'classes': ('collapse',),
                'fields': ('phone_number', 'country', 'city', 'website', 'linkedin_url'),
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + ((
        'Additional Info',
        {
            'fields': ('email', 'role'),
        },
    ),)
