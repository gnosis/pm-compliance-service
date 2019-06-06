import logging

from django.conf import settings
from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from eth_account.account import Account
from rest_framework import filters, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from pm_compliance_service.version import __version__

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if not response:
        if isinstance(exc, Exception):
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
