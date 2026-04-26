from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:course_id>/', views.initiate_payment, name='initiate_payment'),
]
