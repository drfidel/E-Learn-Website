from django.urls import path

from . import views

app_name = 'courses'

urlpatterns = [
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('certificate/issue/<int:enrollment_id>/', views.issue_certificate, name='issue_certificate'),
    path('certificate/<str:certificate_id>/', views.view_certificate, name='view_certificate'),
    path('certificate/verify/<str:certificate_id>/', views.verify_certificate, name='verify_certificate'),
    path('create/', views.course_create, name='course_create'),
]
