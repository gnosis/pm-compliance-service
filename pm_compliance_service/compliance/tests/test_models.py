from django.test import TestCase

from ..models import User
from .factories import UserFactory


class TestModels(TestCase):
    def test_user_model(self):
        self.assertEqual(User.objects.count(), 0)

        # Create user
        UserFactory()
        self.assertEqual(User.objects.count(), 1)
