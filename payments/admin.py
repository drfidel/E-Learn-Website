from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'course',
        'provider',
        'status',
        'amount',
        'created_at',
    )
    list_filter = ('provider', 'status', 'created_at')
    search_fields = (
        'student__email',
        'student__username',
        'course__title',
        'external_reference',
    )
    autocomplete_fields = ('student', 'course')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('student', 'course')
