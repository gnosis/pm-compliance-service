from django.conf import settings
from django.test import TestCase
from eth_account import Account
from gnosis.eth.tests.ethereum_test_case import EthereumTestCaseMixin

from .factories import get_mocked_signup_data
from ..serializers import UserSerializer


class TestSerializers(TestCase, EthereumTestCaseMixin):

    @classmethod
    def setUpTestData(cls):
        cls.prepare_tests()

    def setUp(self):
        self.last_snapshot_idx = self.w3.manager.request_blocking('evm_snapshot', [])

    def tearDown(self):
        self.w3.manager.request_blocking("evm_revert", [self.last_snapshot_idx])

    def test_user_serializer(self):
        ethereum_address = Account.create().address
        custom_data = {'user':{'ethereum_address': ethereum_address}}
        mock_data = get_mocked_signup_data(**custom_data)  # override default data

        self.send_ether(ethereum_address, settings.MIN_SIGNUP_ETH_BALANCE)  # put money on eth address

        serializer = UserSerializer(data=mock_data['user'])
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertIsNotNone(instance)


