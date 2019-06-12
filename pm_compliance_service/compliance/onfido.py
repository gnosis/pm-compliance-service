from typing import Dict
from urllib.parse import urljoin

from requests import post, models
from rest_framework.status import HTTP_201_CREATED

from .constants import ONFIDO_APPLICANT_ENDPOINT


class OnfidoCreationException(Exception):
    pass


class Applicant:
    """
    Incapsulates applicant creation data into an object class.
    """
    def __init__(self, request: models.Response):
        self._data = request.json()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def __str__(self):
        return 'User={} {} Token={}'.format(self._data.get('first_name'), self.data.get('last_name'),
                                            self.data.get('id'))


class Client:
    def __init__(self, base_url: str, token: str):
        self._base_url = base_url
        self._token = token

    def get_auth_header(self) -> Dict:
        return {
            'Authorization': 'Token token=%s' % self._token
        }

    def create_applicant(self, data: dict) -> Applicant:
        """
        Create an applicant on Onfido
        :param data:
        :return: Applicant
        :raises OnfidoCreationError
        """
        onfido_url = urljoin(self._base_url, ONFIDO_APPLICANT_ENDPOINT)
        request = post(onfido_url, data=data, headers=self.get_auth_header())

        if request.status_code == HTTP_201_CREATED:
            return Applicant(request)
        else:
            raise OnfidoCreationException(request.status_code)
