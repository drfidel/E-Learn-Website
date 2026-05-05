from django.urls import path

from . import views

app_name = 'lessons'

urlpatterns = [
    path('<int:pk>/', views.lesson_detail, name='detail'),
    path('course/<int:course_id>/modules/new/', views.module_create, name='module_create'),
    path('module/<int:module_id>/lessons/new/', views.lesson_create, name='lesson_create'),
    path('<int:lesson_id>/quiz/new/', views.quiz_create, name='quiz_create'),
    path('quiz/<int:quiz_id>/questions/new/', views.question_create, name='question_create'),
    path('<int:lesson_id>/progress/', views.toggle_lesson_progress, name='toggle_progress'),
]
