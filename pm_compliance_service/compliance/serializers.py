from gnosis.eth.django.serializers import EthereumAddressField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Country, User


class UserCreationSerializer(serializers.Serializer):
    """
    Serializes user data into database.
    """
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
        address_exists = User.objects.filter(ethereum_address=value).exists()
        if address_exists:
            raise ValidationError
        return value

    def validate_email(self, value):
        email_exists = User.objects.filter(email=value).exists()
        if email_exists:
            raise ValidationError
        return value

    def create(self, validated_data):
        return User.objects.create(**validated_data)

