from django.conf import settings
from gnosis.eth.django.serializers import EthereumAddressField
from gnosis.eth import EthereumClientProvider
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Country, User


class UserCreationSerializer(serializers.ModelSerializer):
    """
    Serializes user data into database.
    """
    class Meta:
        model = User
        fields = ('country', 'email', 'ethereum_address', 'lastname', 'name',)

    country = serializers.CharField(max_length=3, min_length=3)
    email = serializers.EmailField()
    ethereum_address = EthereumAddressField()
    lastname = serializers.CharField()
    name = serializers.CharField()

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
        return User.objects.create(**validated_data)

