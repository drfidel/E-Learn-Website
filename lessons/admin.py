from django.contrib import admin

from .models import Lesson, Module, Question, Quiz


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
    autocomplete_fields = ('course',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'order')
    list_filter = ('content_type', 'module__course')
    search_fields = ('title', 'module__title', 'module__course__title')
    ordering = ('module', 'order')
    autocomplete_fields = ('module',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'pass_mark')
    search_fields = ('title', 'lesson__title', 'lesson__module__course__title')
    autocomplete_fields = ('lesson',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'short_text', 'correct_option')
    list_filter = ('correct_option',)
    search_fields = ('text', 'quiz__title', 'quiz__lesson__title')
    autocomplete_fields = ('quiz',)

    @admin.display(description='Question')
    def short_text(self, obj):
        return obj.text[:70] + '...' if len(obj.text) > 70 else obj.text
