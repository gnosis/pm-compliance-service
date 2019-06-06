from enum import Enum

from django.db import models
from gnosis.eth.django.models import EthereumAddressField
from model_utils.models import TimeStampedModel


class Status(Enum):
    PENDING = 0
    FROZEN = 1
    FAILED = 2
    VERIFIED = 3
    ONBOARDING = 4


class Country(TimeStampedModel):
    name = models.CharField(max_length=45)
    iso2 = models.CharField(max_length=2, primary_key=True)
    iso3 = models.CharField(max_length=3)
    numeric = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class User(TimeStampedModel):
    ethereum_address = EthereumAddressField(unique=True)
    email = models.EmailField(unique=True)
    cra = models.PositiveSmallIntegerField()
    status = models.PositiveSmallIntegerField(null=False, choices=[(tag.value, tag.name) for tag in Status])
    is_source_of_funds_verified = models.BooleanField(default=False)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='country_users')

    def __str__(self):
        return 'Email={} Address={} Status={}'.format(self.email, self.ethereum_address, self.status)
