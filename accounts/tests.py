from django.test import TestCase
from django.urls import reverse

from .models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email='student@example.com', username='student', password='test12345')
        self.assertEqual(user.role, User.Role.STUDENT)


class RegistrationViewTests(TestCase):
    def test_register_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'newstudent@example.com',
                'username': 'newstudent',
                'role': User.Role.STUDENT,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='newstudent@example.com').exists())
        self.assertTrue(response.context['user'].is_authenticated)

    def test_register_does_not_allow_admin_role(self):
        response = self.client.post(
            reverse('accounts:register'),
            {
                'email': 'badrole@example.com',
                'username': 'badrole',
                'role': User.Role.ADMIN,
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='badrole@example.com').exists())

    def test_authenticated_user_is_redirected_from_register(self):
        user = User.objects.create_user(email='loggedin@example.com', username='loggedin', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.get(reverse('accounts:register'))
        self.assertRedirects(response, reverse('home'))


class LoginViewTests(TestCase):
    def test_login_with_uppercase_email_succeeds(self):
        user = User.objects.create_user(
            email='studentlogin@example.com',
            username='studentlogin',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'username': 'STUDENTLOGIN@EXAMPLE.COM', 'password': 'StrongPass123!'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].id, user.id)

    def test_login_with_email_whitespace_succeeds(self):
        user = User.objects.create_user(
            email='spacedlogin@example.com',
            username='spacedlogin',
            password='StrongPass123!',
        )

        response = self.client.post(
            reverse('accounts:login'),
            {'username': '  spacedlogin@example.com  ', 'password': 'StrongPass123!'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].id, user.id)
