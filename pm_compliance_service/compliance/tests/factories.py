from logging import getLogger
from random import randrange

from eth_account import Account
import factory
from faker import Faker
from faker.providers import internet

from ..models import Country, User
from ..utils import country_iso_codes


logger = getLogger(__name__)
# faker = factory.Faker()
faker = Faker()
faker.add_provider(internet)


class CountryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Country

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        country_iso_code = country_iso_codes[randrange(0, len(country_iso_codes))]
        obj.name = country_iso_code[1]
        obj.iso2 = country_iso_code[0]
        obj.iso3 = country_iso_code[2]
        obj.numeric = country_iso_code[3]
        obj.save()
        return obj


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    ethereum_address = factory.LazyFunction(lambda: Account.create().address)
    email = faker.safe_email()
    cra = faker.random.randrange(0, 10)
    status = faker.random.randrange(0, 5)
    is_source_of_funds_verified = False
    country = factory.SubFactory(CountryFactory)
