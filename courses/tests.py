from django.test import TestCase

from accounts.models import User
from .models import Course


class CourseModelTest(TestCase):
    def test_is_free(self):
        instructor = User.objects.create_user(email='inst@example.com', username='inst', password='secret123', role='instructor')
        course = Course.objects.create(instructor=instructor, title='Django', description='x', price=0)
        self.assertTrue(course.is_free)
