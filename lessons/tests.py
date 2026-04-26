from django.test import TestCase

from accounts.models import User
from courses.models import Course
from .models import Lesson, Module


class LessonTest(TestCase):
    def test_module_ordering(self):
        instructor = User.objects.create_user(email='t@example.com', username='t', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Python', description='desc', price=0)
        m1 = Module.objects.create(course=course, title='B', order=2)
        m2 = Module.objects.create(course=course, title='A', order=1)
        self.assertEqual(list(Module.objects.filter(course=course))[0], m2)
        Lesson.objects.create(module=m1, title='L1', content_type='text', text_content='Hello')
