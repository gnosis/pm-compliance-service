from typing import Dict, List

from requests import post
from rest_framework import status

from .base import BaseClient
from ..exceptions import FailedRequestException


class Client(BaseClient):
    endpoints = {
        'prescreening': '/users/{user_id}/withdrawaladdresses/'
    }

    def get_auth_header(self) -> Dict:
        """
        Creates the authorization header to set on each request
        :return: auth header dictionary
        """
        return {
            'Token': self._token
        }

    def post_prescreening(self, address: str, asset: str, user_id: str) -> List[Dict]:
        """
        Triggers `/users/BTC_01/withdrawaladdresses`.
        See: https://docs.chainalysis.com/api/kyt/#withdrawal-pre-screening
        :param user_id: a programmatically generated ID for the user.
        :param asset: name of the cryptocurrency ETH, DAI, etc.
        :param address: Address of the cryptocurrency.
        :return: A list containing a dictionary with the result of AML screening.
        """
        endpoint = self.endpoints['prescreening'].format(user_id=user_id)
        url = f'{self._base_url}{endpoint}'

        data = [{
            'asset': asset,
            'address': address
        }]

        request = post(url, json=data, headers=self.get_auth_header())
        # A correct execution should return 200, otherwise an error has happened.
        if request.status_code != status.HTTP_200_OK:
            raise FailedRequestException(request.status_code)
        return request.json()
