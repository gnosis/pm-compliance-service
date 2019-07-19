from django.conf import settings
from django.utils.module_loading import import_string


def get_aml_client():
    client_class = import_string(settings.AML_CLIENT_CLASS)
    return client_class(settings.AML_CLIENT_BASE_URL, settings.AML_CLIENT_API_TOKEN)
