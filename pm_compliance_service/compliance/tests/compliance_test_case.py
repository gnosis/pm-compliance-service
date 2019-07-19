from typing import Any, Dict, NoReturn

from django.conf import settings
from django.urls import reverse
from eth_account import Account
from gnosis.eth.tests.ethereum_test_case import EthereumTestCaseMixin
from rest_framework import status

from .factories import get_mocked_signup_data
from ..models import User


class ComplianceTestMixin(EthereumTestCaseMixin):
    def create_user(self, amount: int = settings.MIN_SIGNUP_WEI_BALANCE) -> User:
        """
        Creates an user with funds.
        :param amount: amount in ETH to deposit
        :return: instance of User
        """
        # Create address, Balance is 0 ETH
        ethereum_address = Account.create().address
        # Send funds to signing address
        self.send_ether(ethereum_address, amount)

        mock_data = get_mocked_signup_data()
        url = reverse(self.creation_url, kwargs={'ethereum_address': ethereum_address})
        response = self.client.post(url, data=mock_data['user'], format='json')

        assert response.status_code == status.HTTP_201_CREATED

        return User.objects.get(ethereum_address=ethereum_address)
