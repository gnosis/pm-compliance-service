from django.conf import settings
from django.urls import reverse
from eth_account import Account
from gnosis.eth.tests.ethereum_test_case import EthereumTestCaseMixin
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase

from .factories import get_mocked_signup_data
from ..models import User, Status


class TestViews(APITestCase, EthereumTestCaseMixin):

    @classmethod
    def setUpTestData(cls):
        cls.prepare_tests()

    def setUp(self):
        self.last_snapshot_idx = self.w3.manager.request_blocking('evm_snapshot', [])

    def tearDown(self):
        self.w3.manager.request_blocking("evm_revert", [self.last_snapshot_idx])

    def test_user_creation_low_funds(self):
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data()
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Send funds to signing address
        mock_data['user'].update({'giacomo': True})
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_ETH_BALANCE)
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_creation(self):
        ethereum_address = Account.create().address
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_ETH_BALANCE)
        mock_data = get_mocked_signup_data()
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.first().email, mock_data['user']['email'])
        self.assertEqual(User.objects.first().ethereum_address, ethereum_address)
        self.assertEqual(User.objects.first().cra, None)
        self.assertEqual(User.objects.first().status, Status.PENDING.value)

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
        mock_data = get_mocked_signup_data(**{'user': {'email': 'wrong.com'}})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving data with wrong country ISO3 code
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data(**{'user': {'country': '000'}})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data['user']['country'])
        self.assertIsInstance(response.data['user']['country'][0], ErrorDetail)

        # Try saving data empty data
        response = self.client.post(url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
