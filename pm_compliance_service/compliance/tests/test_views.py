from django.urls import reverse
from eth_account import Account
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from .factories import get_mocked_signup_data
from ..models import User


class TestViews(APITestCase):
    def test_user_creation(self):
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data()

        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.first().email, mock_data['email'])
        self.assertEqual(User.objects.first().ethereum_address, ethereum_address)

        # Try saving the same user twice
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving the same data with different ethereum address
        ethereum_address = Account.create().address
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving data with wrong email address
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data(**{'email': 'wrong.com'})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving data with wrong country ISO3 code
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data(**{'country': '000'})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data.get('country', None))
        self.assertIsInstance(response.data.get('country')[0], ErrorDetail)
