from django.test import TestCase

from .models import Review


class ReviewTest(TestCase):
    def test_rating_default(self):
        self.assertEqual(Review._meta.get_field('rating').default, 5)
