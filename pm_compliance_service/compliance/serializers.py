from enum import Enum

from django.conf import settings
from gnosis.eth.django.serializers import EthereumAddressField
from gnosis.eth import EthereumClientProvider
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .onfido import Client, OnfidoCreationException
from .models import Country, User


class SourceOfWealth(Enum):
    SALARIED = 0
    SELF_EMPLOYEE = 1
    GIFT = 2
    PENSION = 3
    FINANCIAL_TRADING = 4
    TAX_REBATES = 5
    CRYPTOCURRENCY_TRADING = 6
    SALFE_OF_INVESTEMENTS = 7
    SALE_OF_PROPERTY = 8
    SALFE_OF_COMPANY = 9
    RENTAL_INCOME = 10


class UserSerializer(serializers.Serializer):
    """
    Serializes user data into database.
    """
    country = serializers.CharField(max_length=3, min_length=3)
    email = serializers.EmailField()
    ethereum_address = EthereumAddressField()
    lastname = serializers.CharField()
    name = serializers.CharField()
    source_of_wealth = serializers.ChoiceField([(tag.value, tag.name) for tag in SourceOfWealth])
    source_of_wealth_metadata = serializers.CharField(max_length=255)
    expected_trade_volume = serializers.IntegerField()

    def validate_country(self, value):
        try:
            value = value.upper()
            country = Country.objects.get(iso3=value)
            # Country must be enabled to allow users to signup
            if not country.is_enabled:
                raise ValidationError('Country ISO3 {} not enabled'.format(value))
        except Country.DoesNotExist as e:
            raise ValidationError('Invalid Country ISO3 code {}'.format(value)) from e

        return country

    def validate_ethereum_address(self, value):
        eth_client = EthereumClientProvider()
        address_exists = User.objects.filter(ethereum_address=value).exists()
        if address_exists:
            raise ValidationError

        # Validate that provided ethereum address has enough balance
        eth_balance = eth_client.get_balance(value)
        if eth_balance < settings.MIN_SIGNUP_ETH_BALANCE:
            raise ValidationError('Minimum Ethereum balance is {}, current account balance {}'.format(
                settings.MIN_SIGNUP_ETH_BALANCE, eth_balance))
        return value

    def validate_email(self, value):
        email_exists = User.objects.filter(email=value).exists()
        if email_exists:
            raise ValidationError
        return value

    def create(self, validated_data):
        user_data = {
            'name': validated_data['name'],
            'lastname': validated_data['lastname'],
            'country': validated_data['country'],
            'ethereum_address': validated_data['ethereum_address'],
            'email': validated_data['email']
        }
        return User.objects.create(**user_data)


class OnfidoSerializer(serializers.Serializer):
    """
    Serializes data that will be sent to 3rd-party services.
    """
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dob = serializers.DateField(allow_null=True)

    def create(self, validated_data):
        # Instantiate onfido client
        onfido_client = Client(settings.ONFIDO_BASE_URL, settings.ONFIDO_API_TOKEN)

        try:
            applicant = onfido_client.create_applicant(validated_data)
        except OnfidoCreationException as exc:
            raise ValidationError from exc

        return applicant
