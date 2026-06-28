from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from lessons.models import Lesson, Module
from .models import Certificate, Course, Enrollment, Progress


class CourseModelTest(TestCase):
    def test_is_free(self):
        instructor = User.objects.create_user(email='inst@example.com', username='inst', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Django', description='x', price=0)
        self.assertTrue(course.is_free)


class EnrollmentFlowTests(TestCase):
    def test_free_course_enroll_creates_enrollment(self):
        instructor = User.objects.create_user(email='inst2@example.com', username='inst2', password='secret123', role='instructor')
        student = User.objects.create_user(email='stud@example.com', username='stud', password='secret123', role='student')
        course = Course.objects.create(instructor=instructor, title='Free Course', description='x', price=0)
        self.client.force_login(student)

        response = self.client.post(reverse('courses:enroll_course', args=[course.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(student=student, course=course).exists())

    def test_certificate_not_issued_before_completion(self):
        instructor = User.objects.create_user(email='inst3@example.com', username='inst3', password='secret123', role='instructor')
        student = User.objects.create_user(email='stud2@example.com', username='stud2', password='secret123', role='student')
        course = Course.objects.create(instructor=instructor, title='Course A', description='x', price=0)
        module = Module.objects.create(course=course, title='M1', order=1)
        lesson = Lesson.objects.create(module=module, title='L1', content_type='text', text_content='x', order=1)
        enrollment = Enrollment.objects.create(student=student, course=course)
        Progress.objects.create(enrollment=enrollment, lesson=lesson, completed=False)
        self.client.force_login(student)

        response = self.client.post(reverse('courses:issue_certificate', args=[enrollment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Certificate.objects.filter(enrollment=enrollment).exists())

    def test_certificate_issued_after_completion(self):
        instructor = User.objects.create_user(email='inst4@example.com', username='inst4', password='secret123', role='instructor')
        student = User.objects.create_user(email='stud3@example.com', username='stud3', password='secret123', role='student')
        course = Course.objects.create(instructor=instructor, title='Course B', description='x', price=0)
        module = Module.objects.create(course=course, title='M1', order=1)
        lesson = Lesson.objects.create(module=module, title='L1', content_type='text', text_content='x', order=1)
        enrollment = Enrollment.objects.create(student=student, course=course)
        Progress.objects.create(enrollment=enrollment, lesson=lesson, completed=True)
        self.client.force_login(student)

        response = self.client.post(reverse('courses:issue_certificate', args=[enrollment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Certificate.objects.filter(enrollment=enrollment).exists())
