from django.urls import path

from . import views

urlpatterns = [
    path('', views.course_list, name='home'),
    path('about/', views.about, name='about'),
    path('cookies/', views.cookies, name='cookies'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
]
