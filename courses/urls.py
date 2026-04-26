from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('create/', views.course_create, name='course_create'),
]
