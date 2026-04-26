from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import CourseDetailAPIView, CourseListAPIView, EnrollAPIView, ReviewListCreateAPIView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('courses/', CourseListAPIView.as_view(), name='api_courses'),
    path('courses/<int:pk>/', CourseDetailAPIView.as_view(), name='api_course_detail'),
    path('courses/<int:course_id>/enroll/', EnrollAPIView.as_view(), name='api_enroll'),
    path('reviews/', ReviewListCreateAPIView.as_view(), name='api_reviews'),
]
