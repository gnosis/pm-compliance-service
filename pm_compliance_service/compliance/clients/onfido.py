import logging, random
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from requests import post, models
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from pm_compliance_service.compliance.constants import ONFIDO_APPLICANT_ENDPOINT, ONFIDO_SDK_TOKEN_ENDPOINT
from pm_compliance_service.compliance.exceptions import GenericAPIException
from .base import BaseClient


logger = logging.getLogger(__name__)


class OnfidoCreationException(GenericAPIException):
    def __init__(self, detail, code=None, status_code=None):
        if isinstance(detail, dict) and 'error' in detail and detail['error']['type'] == 'validation_error':
            detail = {'non_fields_error': ['Onfido rejected the request due to invalid incoming data or SDK settings']}

        super().__init__(detail, code=code, status_code=status_code)


class Applicant:
    """
    Incapsulates applicant creation data into an object class.
    """
    def __init__(self, request: models.Response, sdk_token: str = None):
        self._data = request.json()
        self._sdk_token = sdk_token

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @property
    def sdk_token(self):
        return self._sdk_token

    @sdk_token.setter
    def sdk_token(self, sdk_token):
        self._sdk_token = sdk_token

    def __str__(self):
        return 'User={} {} Token={}'.format(self._data.get('first_name'), self.data.get('last_name'),
                                            self.data.get('id'))


class Client(BaseClient):
    def create_applicant(self, data: dict) -> Applicant:
        """
        Creates an applicant on Onfido
        :param data:
        :return: Applicant
        :raises OnfidoCreationError
        """
        onfido_url = urljoin(self._base_url, ONFIDO_APPLICANT_ENDPOINT)
        request = post(onfido_url, data=data, headers=self.get_auth_header())

        if request.status_code == HTTP_201_CREATED:
            return Applicant(request)
        else:
            logger.warning(request.json())
            raise OnfidoCreationException(detail=request.json())

    def get_sdk_token(self, data: dict) -> str:
        """
        Returns an onfido SDK token for the applicant id given in input
        :param data: See https://documentation.onfido.com/#generate-web-sdk-token
        :return: sdk token
        """
        onfido_url = urljoin(self._base_url, ONFIDO_SDK_TOKEN_ENDPOINT)
        request = post(onfido_url, data=data, headers=self.get_auth_header())

        if request.status_code == HTTP_200_OK:
            return request.json().get('token')
        else:
            logger.warning(request.json())
            raise OnfidoCreationException(detail=request.json())


class DummyClient(Client):
    def get_id(self):
        return ''.join(random.choices('ABCDEF' + '123456', k=5))

    def get_created_at(self, format='%m-%d-%yT%H:%M:%SZ'):
        return datetime.now().strftime(format)

    def create_applicant(self, data: dict) -> Applicant:
        def dummyinit(*args): pass

        # Create a class at runtime and override Applicant.__init__()
        applicant_cls = type('DummyApplicant', (Applicant,), {'__init__': dummyinit})
        # Instantiate class
        applicant = applicant_cls()
        applicant.data = {
            'id': self.get_id(),
            'created_at': self.get_created_at()
        }

        return applicant

    def get_sdk_token(self, data: dict) -> str:
        return self.get_id()


def get_client(base_url: str, api_token: str):
    """
    Returns an instance of Onfido Client if settings.ONFIDO_TEST_CLIENT is not set or False, DummyClient otherwise.
    :param base_url: See settings.ONFIDO_BASE_URL
    :param api_token: See settings.ONFIDO_API_TOKEN
    :return: Client
    """
    if hasattr(settings, 'ONFIDO_TEST_CLIENT') and settings.ONFIDO_TEST_CLIENT:
        return DummyClient(base_url, api_token)
    return Client(base_url, api_token)