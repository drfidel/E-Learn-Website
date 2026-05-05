from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('course__title', 'student__email', 'student__username', 'comment')
    autocomplete_fields = ('course', 'student')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('course', 'student')
