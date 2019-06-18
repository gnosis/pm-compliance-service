from django.conf import settings
from django.test import override_settings
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
        # Create address, Balance is 0 ETH
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data()
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_data['user'].update({'giacomo': True})
        # Send funds to signing address
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_WEI_BALANCE)
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_creation(self):
        # Create address, Balance is 0 ETH
        ethereum_address = Account.create().address
        # Send funds to signing address
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_WEI_BALANCE)
        mock_data = get_mocked_signup_data()
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.first().email, mock_data['user']['email'])
        self.assertEqual(User.objects.first().ethereum_address, ethereum_address)
        self.assertEqual(User.objects.first().cra, None)
        self.assertEqual(User.objects.first().status, Status.PENDING.value)

        # Try saving the same user twice
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving the same data with different ethereum address
        ethereum_address = Account.create().address
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving data with wrong email address
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data(**{'user': {'email': 'wrong.com'}})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try saving data with wrong country ISO3 code
        ethereum_address = Account.create().address
        mock_data = get_mocked_signup_data(**{'user': {'country': '000'}})
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data['country'])
        self.assertIsInstance(response.data['country'][0], ErrorDetail)

        # Try saving data empty data
        response = self.client.post(url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        ONFIDO_API_TOKEN=None,
        ONFIDO_TEST_CLIENT=False  # check against real API
    )
    def test_user_creation_wrong_onfido_api_token(self):
        ethereum_address = Account.create().address
        # Send funds to signing address
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_WEI_BALANCE)
        mock_data = get_mocked_signup_data()
        self.assertEqual(User.objects.count(), 0)
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    @override_settings(
        ENABLE_RECAPTCHA_VALIDATION=True
    )
    def test_user_creation_invalid_recaptcha(self):
        ethereum_address = Account.create().address
        # Send funds to signing address
        self.send_ether(ethereum_address, settings.MIN_SIGNUP_WEI_BALANCE)
        mock_data = get_mocked_signup_data()
        url = reverse('v1:user-creation', kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.data['recaptcha'][0], ErrorDetail)
