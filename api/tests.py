from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from courses.models import Certificate, Course, Enrollment
from lessons.models import Lesson, Module


class CourseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='api@t.com', username='api', password='secret123', role='instructor')
        self.client.force_authenticate(self.user)

    def test_create_course(self):
        response = self.client.post(reverse('api_courses'), {'title': 'API Course', 'description': 'D', 'price': '0.00'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Course.objects.count(), 1)

    def test_module_and_lesson_endpoints(self):
        course = Course.objects.create(instructor=self.user, title='API Course', description='D')

        module_response = self.client.post(reverse('api_modules'), {'course': course.id, 'title': 'Basics', 'order': 1})
        self.assertEqual(module_response.status_code, 201)
        module = Module.objects.get()

        lesson_response = self.client.post(
            reverse('api_lessons'),
            {'module': module.id, 'title': 'Intro', 'content_type': 'text', 'text_content': 'Hello', 'order': 1},
        )
        self.assertEqual(lesson_response.status_code, 201)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_student_can_track_progress_and_claim_certificate(self):
        student = User.objects.create_user(email='student@t.com', username='student', password='secret123', role='student')
        course = Course.objects.create(instructor=self.user, title='API Course', description='D', is_published=True)
        module = Module.objects.create(course=course, title='Basics')
        lesson = Lesson.objects.create(module=module, title='Intro', content_type='text', text_content='Hello')
        enrollment = Enrollment.objects.create(student=student, course=course)
        self.client.force_authenticate(student)

        progress_response = self.client.post(reverse('api_lesson_progress', args=[lesson.id]), {'completed': True})
        self.assertEqual(progress_response.status_code, 200)

        certificate_response = self.client.post(reverse('api_issue_certificate', args=[enrollment.id]))
        self.assertEqual(certificate_response.status_code, 201)
        self.assertTrue(Certificate.objects.filter(enrollment=enrollment).exists())

    def test_register_endpoint_creates_student(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse('api_register'),
            {
                'email': 'new@t.com',
                'username': 'newbie',
                'password': 'secret123',
                'role': 'student',
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email='new@t.com').exists())
