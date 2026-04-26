from django.contrib import admin

from .models import Lesson, Module, Question, Quiz

admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Quiz)
admin.site.register(Question)
