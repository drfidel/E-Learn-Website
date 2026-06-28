from django.contrib import admin
from django.db.models import Avg, Count

from .models import Category, Certificate, Course, Enrollment, Progress


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'instructor',
        'category',
        'price',
        'is_published',
        'students_count',
        'average_rating',
        'created_at',
    )
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__email', 'instructor__username')
    autocomplete_fields = ('instructor', 'category')
    date_hierarchy = 'created_at'
    list_select_related = ('instructor', 'category')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            _students_count=Count('enrollments', distinct=True),
            _average_rating=Avg('reviews__rating'),
        )

    @admin.display(description='Students', ordering='_students_count')
    def students_count(self, obj):
        return obj._students_count

    @admin.display(description='Rating', ordering='_average_rating')
    def average_rating(self, obj):
        return f"{obj._average_rating:.1f}/5" if obj._average_rating else '-'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'created_at')
    list_filter = ('created_at', 'course')
    search_fields = ('student__email', 'student__username', 'course__title')
    autocomplete_fields = ('student', 'course')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_select_related = ('student', 'course')


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'completed', 'completed_at')
    list_filter = ('completed', 'completed_at')
    search_fields = (
        'enrollment__student__email',
        'enrollment__course__title',
        'lesson__title',
    )
    autocomplete_fields = ('enrollment', 'lesson')
    ordering = ('-completed_at',)
    list_select_related = ('enrollment', 'lesson')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'enrollment', 'issued_at')
    search_fields = (
        'certificate_id',
        'enrollment__student__email',
        'enrollment__course__title',
    )
    autocomplete_fields = ('enrollment',)
    date_hierarchy = 'issued_at'
    ordering = ('-issued_at',)
    readonly_fields = ('certificate_id', 'issued_at')
