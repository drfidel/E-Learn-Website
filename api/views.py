from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course, Enrollment
from payments.models import Payment
from reviews.models import Review
from .serializers import CourseSerializer, EnrollmentSerializer, ReviewSerializer


class CourseListAPIView(generics.ListCreateAPIView):
    queryset = Course.objects.select_related('instructor').all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class CourseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.select_related('instructor').all()
    serializer_class = CourseSerializer


class EnrollAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = generics.get_object_or_404(Course, id=course_id)
        if course.price > 0 and not Payment.objects.filter(course=course, student=request.user, status='success').exists():
            return Response({'detail': 'Payment required.'}, status=402)
        enrollment, _ = Enrollment.objects.get_or_create(course=course, student=request.user)
        return Response(EnrollmentSerializer(enrollment).data)


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all().select_related('student', 'course')
    serializer_class = ReviewSerializer
