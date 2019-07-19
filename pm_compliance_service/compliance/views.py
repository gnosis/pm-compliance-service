import logging
from typing import Dict

import requests
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler
from web3 import Web3

from pm_compliance_service.version import __version__
from .constants import RECAPTCHA_RESPONSE_PARAM
from .models import User
from .serializers import AmlScreeningSerializer, OnfidoSerializer, UserCreationSerializer, UserDetailSerializer
from .tasks import aml_prescreening_task


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if not response:
        if isinstance(exc, ObjectDoesNotExist):
            response = Response(status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, Exception):
            response = Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            response = Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if str(exc):
            exception_str = '{}: {}'.format(exc.__class__.__name__, exc)
        else:
            exception_str = exc.__class__.__name__
        response.data = {'exception':  exception_str}

        logger.warning('%s - Exception: %s - Data received %s' % (context['request'].build_absolute_uri(),
                                                                  exception_str,
                                                                  context['request'].data))
    return response


class AboutView(APIView):
    """
    Returns relevant information about the project itself.
    """
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        content = {
            'name': 'PM Compliance Service',
            'version': __version__,
            'api_version': self.request.version,
            'https_detected': self.request.is_secure(),
            'settings': {}
        }
        return Response(content)


class UserView(APIView):
    """
    Handles requests to /users/<str:ethereum_address>
    """
    permission_classes = (AllowAny,)
    serializer_class = UserCreationSerializer

    def _transform_data(self, ethereum_address: str, data: Dict) -> Dict:
        """
        Transform input data into a structure compatible with UserCreationSerializer
        :return transformed data dictionary
        """
        logger.debug('Transform data for address={} data={}'.format(ethereum_address, data))

        transformed_data = {
            'user': {
                **data,
                'ethereum_address': ethereum_address,
                'recaptcha': data.get(RECAPTCHA_RESPONSE_PARAM, None)
            }
        }

        transformed_data.update({
            'onfido': {
                'first_name': transformed_data['user'].get('name', None),
                'last_name': transformed_data['user'].get('lastname', None),
                'email': transformed_data['user'].get('email', None),
                'dob': transformed_data['user'].get('birthdate', None),
                'country': transformed_data['user'].get('country', None)
            }
        })

        logger.debug('Transformed data={}'.format(transformed_data))

        return transformed_data

    def _is_recaptcha_valid(self, recaptcha: str) -> bool:
        """
        Executes recaptcha validation.
        :param recaptcha
        :return: True if recaptcha_value is valid, False otherwise
        """
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha
        }

        # Execute captcha validation
        request = requests.post(settings.RECAPTCHA_VALIDATION_URL, data=data)
        return request.json().get('success') is True

    @swagger_auto_schema(responses={201: UserCreationSerializer(),
                                    400: 'Invalid data',
                                    422: 'Unprocessable Ethereum address'})
    def post(self, request, ethereum_address, *args, **kwargs):
        if not Web3.isChecksumAddress(ethereum_address):
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Transform data
        transformed_data = self._transform_data(ethereum_address, request.data)

        # Validate recaptcha
        if settings.ENABLE_RECAPTCHA_VALIDATION:
            logger.debug('Verify RECAPTCHA code')
            if not self._is_recaptcha_valid(transformed_data.get('user')['recaptcha']):
                # Raise a django compliant validation error
                raise ValidationError({'recaptcha': ['Invalid recaptcha code']})

        user_serializer = self.serializer_class(data=transformed_data.get('user'))
        if user_serializer.is_valid():
            # Wrap execution into a transaction
            with transaction.atomic():
                logger.debug('Create user: {}'.format(transformed_data.get('user')))
                # Save user on database
                user_serializer.save()

                logger.debug('Create onfido entry: {}'.format(transformed_data.get('onfido')))
                # Instantiate onfido serializer
                onfido_serializer = OnfidoSerializer(data=transformed_data.get('onfido'))
                onfido_serializer.is_valid(raise_exception=True)

                logger.debug('Create onfido applicant: {}'.format(transformed_data.get('onfido')))
                applicant = onfido_serializer.save()

                logger.debug('Applicant created {}'.format(applicant.data))

                # Create response data starting from Applicant instance data
                response_data = {
                    **applicant.data,
                    'sdk_token': applicant.sdk_token
                }
                return Response(status=status.HTTP_201_CREATED, data=response_data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=user_serializer.errors)

    @swagger_auto_schema(responses={200: UserDetailSerializer,
                                    404: 'User not found',
                                    422: 'Unprocessable Ethereum address'})
    def get(self, request, ethereum_address, *args, **kwargs):
        if not Web3.isChecksumAddress(ethereum_address):
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            user = User.objects.get(ethereum_address=ethereum_address)
            # Create return data
            data = UserDetailSerializer(user).data
            return Response(status=status.HTTP_200_OK, data=data)
        except User.DoesNotExist as exc:
            raise exc


@swagger_auto_schema(responses={201: AmlScreeningSerializer,
                                400: 'Invalid request',
                                422: 'Unprocessable Ethereum address'})
class AmlScreeningView(APIView):
    """
    Handles requests to /aml/screening/<str:ethereum_address>
    """
    permission_classes = (AllowAny,)  # TODO implement authentication
    serializer_class = AmlScreeningSerializer

    def post(self, request, ethereum_address, *args, **kwargs):
        if not Web3.isChecksumAddress(ethereum_address):
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        data = request.data.copy()
        # Make address available to serializer
        data['address'] = ethereum_address

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            aml_prescreening_task.delay(data['address'], data['asset'], data['user_id'])
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
