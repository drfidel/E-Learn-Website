from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:course_id>/', views.add_review, name='add_review'),
    path('manage/<int:course_id>/', views.manage_reviews, name='manage_reviews'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
]
