from rest_framework import serializers

from accounts.models import User
from courses.models import Category, Certificate, Course, Enrollment, Progress
from lessons.models import Lesson, Module, Question, Quiz
from payments.models import Payment
from reviews.models import Review


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'photo',
            'headline',
            'phone_number',
            'country',
            'city',
            'website',
            'linkedin_url',
            'bio',
            'learning_goals',
            'qualifications',
            'is_instructor_approved',
        ]
        read_only_fields = ['id', 'role', 'is_instructor_approved']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError('Admin users cannot be created through public registration.')
        return value


class CategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'courses_count']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'module', 'title', 'content_type', 'video_url', 'text_content', 'file', 'order']


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True,
    )
    modules = ModuleSerializer(many=True, read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'thumbnail',
            'price',
            'is_free',
            'is_published',
            'category',
            'category_id',
            'instructor',
            'modules',
            'students_count',
            'average_rating',
            'created_at',
        ]
        read_only_fields = ['id', 'instructor', 'created_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source='course', write_only=True)
    student = UserSerializer(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    completed_lessons = serializers.IntegerField(read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id',
            'student',
            'course',
            'course_id',
            'created_at',
            'total_lessons',
            'completed_lessons',
            'progress_percent',
        ]
        read_only_fields = ['id', 'student', 'created_at']


class ProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    lesson_id = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), source='lesson', write_only=True)

    class Meta:
        model = Progress
        fields = ['id', 'enrollment', 'lesson', 'lesson_id', 'completed', 'completed_at']
        read_only_fields = ['id', 'enrollment', 'completed_at']


class CertificateSerializer(serializers.ModelSerializer):
    student = UserSerializer(source='enrollment.student', read_only=True)
    course = CourseSerializer(source='enrollment.course', read_only=True)

    class Meta:
        model = Certificate
        fields = ['id', 'certificate_id', 'enrollment', 'student', 'course', 'issued_at']
        read_only_fields = ['id', 'certificate_id', 'enrollment', 'student', 'course', 'issued_at']


class ReviewSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'course', 'student', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'student', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'lesson', 'title', 'pass_mark', 'questions']


class PaymentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source='course', write_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'student',
            'course',
            'course_id',
            'provider',
            'external_reference',
            'amount',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'student', 'amount', 'status', 'created_at']
