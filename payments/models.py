from django.conf import settings
from django.db import models


class Payment(models.Model):
    class Provider(models.TextChoices):
        STRIPE = 'stripe', 'Stripe'
        FLUTTERWAVE = 'flutterwave', 'Flutterwave'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=Provider.choices)
    external_reference = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
