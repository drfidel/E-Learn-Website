from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from courses.models import Course


class CourseAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='api@t.com', username='api', password='secret123', role='instructor')
        self.client.force_authenticate(self.user)

    def test_create_course(self):
        response = self.client.post(reverse('api_courses'), {'title': 'API Course', 'description': 'D', 'price': '0.00'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Course.objects.count(), 1)
