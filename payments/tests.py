from django.test import TestCase

from .models import Payment


class PaymentTest(TestCase):
    def test_status_default(self):
        self.assertEqual(Payment.Status.PENDING, 'pending')
