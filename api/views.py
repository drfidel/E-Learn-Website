from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from courses.models import Category, Certificate, Course, Enrollment, Progress
from lessons.models import Lesson, Module, Question, Quiz
from payments.models import Payment
from payments.services import verify_payment
from reviews.models import Review
from .serializers import (
    CategorySerializer,
    CertificateSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    LessonSerializer,
    ModuleSerializer,
    PaymentSerializer,
    ProgressSerializer,
    QuestionSerializer,
    QuizSerializer,
    RegisterSerializer,
    ReviewSerializer,
    UserSerializer,
)


def _is_instructor_or_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or user.is_superuser or user.role in [User.Role.ADMIN, User.Role.INSTRUCTOR])
    )


def _can_manage_course(user, course):
    return bool(
        user
        and user.is_authenticated
        and (user.is_staff or user.is_superuser or user.role == User.Role.ADMIN or course.instructor_id == user.id)
    )


def _progress_counts(enrollment):
    total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
    completed_lessons = enrollment.progress.filter(completed=True).count()
    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0
    return total_lessons, completed_lessons, progress_percent


def _with_progress_counts(enrollment):
    total_lessons, completed_lessons, progress_percent = _progress_counts(enrollment)
    enrollment.total_lessons = total_lessons
    enrollment.completed_lessons = completed_lessons
    enrollment.progress_percent = progress_percent
    return enrollment


class InstructorOrAdminWritePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_instructor_or_admin(request.user)


class CourseContentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return _is_instructor_or_admin(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        course = getattr(obj, 'course', None) or getattr(getattr(obj, 'module', None), 'course', None)
        if isinstance(obj, Quiz):
            course = obj.lesson.module.course
        if isinstance(obj, Question):
            course = obj.quiz.lesson.module.course
        return _can_manage_course(request.user, course)


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [InstructorOrAdminWritePermission]

    def get_queryset(self):
        return Category.objects.annotate(courses_count=Count('course')).order_by('name')


class CourseListAPIView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [InstructorOrAdminWritePermission]

    def get_queryset(self):
        queryset = (
            Course.objects.select_related('instructor', 'category')
            .prefetch_related('modules__lessons')
            .annotate(students_count=Count('enrollments', distinct=True), average_rating=Avg('reviews__rating'))
            .order_by('-created_at')
        )
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser or user.role == User.Role.ADMIN):
            pass
        elif user.is_authenticated:
            queryset = queryset.filter(Q(is_published=True) | Q(instructor=user))
        else:
            queryset = queryset.filter(is_published=True)

        search = self.request.query_params.get('search') or self.request.query_params.get('q')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        pricing = self.request.query_params.get('pricing')
        if pricing == 'free':
            queryset = queryset.filter(price=0)
        elif pricing == 'paid':
            queryset = queryset.exclude(price=0)

        return queryset

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class CourseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [InstructorOrAdminWritePermission]

    def get_queryset(self):
        return (
            Course.objects.select_related('instructor', 'category')
            .prefetch_related('modules__lessons')
            .annotate(students_count=Count('enrollments', distinct=True), average_rating=Avg('reviews__rating'))
        )

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in permissions.SAFE_METHODS and not _can_manage_course(request.user, obj):
            self.permission_denied(request, message='You can only modify your own courses.')


class ModuleListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [CourseContentPermission]

    def get_queryset(self):
        queryset = Module.objects.select_related('course').prefetch_related('lessons').order_by('course_id', 'order')
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if not _can_manage_course(self.request.user, course):
            self.permission_denied(self.request, message='You can only add modules to your own courses.')
        serializer.save()


class ModuleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Module.objects.select_related('course').prefetch_related('lessons')
    serializer_class = ModuleSerializer
    permission_classes = [CourseContentPermission]


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [CourseContentPermission]

    def get_queryset(self):
        queryset = Lesson.objects.select_related('module', 'module__course').order_by('module_id', 'order')
        module_id = self.request.query_params.get('module')
        course_id = self.request.query_params.get('course')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        if course_id:
            queryset = queryset.filter(module__course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        module = serializer.validated_data['module']
        if not _can_manage_course(self.request.user, module.course):
            self.permission_denied(self.request, message='You can only add lessons to your own courses.')
        serializer.save()


class LessonDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.select_related('module', 'module__course')
    serializer_class = LessonSerializer
    permission_classes = [CourseContentPermission]


class QuizListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [CourseContentPermission]

    def get_queryset(self):
        queryset = Quiz.objects.select_related('lesson', 'lesson__module', 'lesson__module__course').prefetch_related('questions')
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        if not _can_manage_course(self.request.user, lesson.module.course):
            self.permission_denied(self.request, message='You can only add quizzes to your own courses.')
        serializer.save()


class QuizDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.select_related('lesson', 'lesson__module', 'lesson__module__course').prefetch_related('questions')
    serializer_class = QuizSerializer
    permission_classes = [CourseContentPermission]


class QuestionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [CourseContentPermission]

    def get_queryset(self):
        queryset = Question.objects.select_related('quiz', 'quiz__lesson', 'quiz__lesson__module')
        quiz_id = self.request.query_params.get('quiz')
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        return queryset

    def perform_create(self, serializer):
        quiz = serializer.validated_data['quiz']
        if not _can_manage_course(self.request.user, quiz.lesson.module.course):
            self.permission_denied(self.request, message='You can only add questions to your own courses.')
        serializer.save()


class QuestionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.select_related('quiz', 'quiz__lesson', 'quiz__lesson__module')
    serializer_class = QuestionSerializer
    permission_classes = [CourseContentPermission]


class EnrollAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, course_id):
        course = generics.get_object_or_404(Course, id=course_id)
        if course.price > 0 and not Payment.objects.filter(course=course, student=request.user, status='success').exists():
            return Response({'detail': 'Payment required.'}, status=402)
        enrollment, _ = Enrollment.objects.get_or_create(course=course, student=request.user)
        return Response(EnrollmentSerializer(_with_progress_counts(enrollment)).data)


class EnrollmentListAPIView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Enrollment.objects.select_related('student', 'course', 'course__instructor', 'course__category').prefetch_related(
            'progress',
            'course__modules__lessons',
        )
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.INSTRUCTOR:
            return queryset.filter(course__instructor=user)
        return queryset.filter(student=user)

    def list(self, request, *args, **kwargs):
        enrollments = [_with_progress_counts(enrollment) for enrollment in self.get_queryset()]
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


class ProgressListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Progress.objects.filter(enrollment__student=self.request.user).select_related('enrollment', 'lesson')

    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        enrollment = generics.get_object_or_404(Enrollment, student=self.request.user, course=lesson.module.course)
        progress, _ = Progress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        completed = serializer.validated_data.get('completed', False)
        progress.completed = completed
        progress.completed_at = timezone.now() if completed else None
        progress.save(update_fields=['completed', 'completed_at'])
        serializer.instance = progress


class LessonProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = generics.get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
        enrollment = generics.get_object_or_404(Enrollment, student=request.user, course=lesson.module.course)
        progress, _ = Progress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        completed = request.data.get('completed', True)
        if isinstance(completed, str):
            completed = completed.lower() in ['1', 'true', 'yes', 'on']
        progress.completed = bool(completed)
        progress.completed_at = timezone.now() if progress.completed else None
        progress.save(update_fields=['completed', 'completed_at'])

        total_lessons, completed_lessons, _ = _progress_counts(enrollment)
        if total_lessons > 0 and completed_lessons == total_lessons:
            Certificate.objects.get_or_create(enrollment=enrollment)

        return Response(ProgressSerializer(progress).data)


class CertificateListAPIView(generics.ListAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Certificate.objects.select_related('enrollment__student', 'enrollment__course__instructor', 'enrollment__course__category')
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.INSTRUCTOR:
            return queryset.filter(enrollment__course__instructor=user)
        return queryset.filter(enrollment__student=user)


class CertificateIssueAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, enrollment_id):
        enrollment = generics.get_object_or_404(Enrollment.objects.select_related('course'), id=enrollment_id, student=request.user)
        total_lessons, completed_lessons, _ = _progress_counts(enrollment)
        if total_lessons == 0 or completed_lessons < total_lessons:
            return Response({'detail': 'Complete all lessons before claiming a certificate.'}, status=status.HTTP_400_BAD_REQUEST)
        certificate, _ = Certificate.objects.get_or_create(enrollment=enrollment)
        return Response(CertificateSerializer(certificate).data, status=status.HTTP_201_CREATED)


class CertificateVerifyAPIView(generics.RetrieveAPIView):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'certificate_id'
    queryset = Certificate.objects.select_related('enrollment__student', 'enrollment__course__instructor', 'enrollment__course__category')


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.all().select_related('student', 'course')
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if not Enrollment.objects.filter(student=self.request.user, course=course).exists():
            self.permission_denied(self.request, message='Enroll in this course before reviewing it.')
        serializer.save(student=self.request.user)


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.select_related('student', 'course', 'course__instructor', 'course__category')
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.INSTRUCTOR:
            return queryset.filter(course__instructor=user)
        return queryset.filter(student=user)

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        payment = serializer.save(student=self.request.user, amount=course.price)
        if verify_payment(payment):
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=['status'])
            Enrollment.objects.get_or_create(student=self.request.user, course=course)
