from django.test import TestCase

from .models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email='student@example.com', username='student', password='test12345')
        self.assertEqual(user.role, User.Role.STUDENT)
