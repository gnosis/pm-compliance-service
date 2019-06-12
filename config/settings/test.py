"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env


env.read_env(str(ROOT_DIR.path('.env_test')))


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY", default="q8lVkJGsIiHcTSQKaWIBsMVPOGnCnF6f7NDGup8KdDNmviSaZVhP0Nq3q3MolmFU")
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": ""
    }
}

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = "localhost"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# CELERY
CELERY_ALWAYS_EAGER = True

# Ethereum
# ------------------------------------------------------------------------------
ETHEREUM_TEST_PRIVATE_KEY = env.str('ETHEREUM_TEST_PRIVATE_KEY', default=None)

# Google
# ------------------------------------------------------------------------------
ENABLE_RECAPTCHA_VALIDATION = env.bool('ENABLE_RECAPTCHA_VALIDATION')

# Onfido
# ------------------------------------------------------------------------------
ONFIDO_API_TOKEN = env.str('ONFIDO_API_TOKEN')
