import logging
from enum import Enum

from django.conf import settings
from gnosis.eth.django.serializers import EthereumAddressField
from gnosis.eth import EthereumClientProvider
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from web3 import Web3

from pm_compliance_service.compliance.clients.onfido import get_client
from .models import Country, User


logger = logging.getLogger(__name__)


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


class AmlScreeningSerializer(serializers.Serializer):
    address = EthereumAddressField()
    asset = serializers.CharField()
    user_id = serializers.IntegerField()

    def validate_address(self, value):
        user_exists = User.objects.filter(ethereum_address=value).exists()
        if not user_exists:
            raise ValidationError('Unknown address')
        return value


class OnfidoSerializer(serializers.Serializer):
    """
    Serializes data that will be sent to 3rd-party services.
    """
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    dob = serializers.DateField(allow_null=True)

    def create(self, validated_data):
        # Get an instance of Onfido Client
        onfido_client = get_client(settings.ONFIDO_BASE_URL, settings.ONFIDO_API_TOKEN)

        logger.debug('Create applicant with data={}'.format(validated_data))
        applicant = onfido_client.create_applicant(validated_data)

        logger.debug('Get SDK Token')
        # Get onfido sdk token
        sdk_token = onfido_client.get_sdk_token({
            'applicant_id': applicant.data.get('id'),
            'referrer': settings.ONFIDO_API_REFERRER
        })

        # Set sdk_token in Applicant instance
        applicant.sdk_token = sdk_token

        return applicant


class UserCreationSerializer(serializers.Serializer):
    """
    Deserializes user data into database.
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
        if eth_balance < settings.MIN_SIGNUP_WEI_BALANCE:
            raise ValidationError('Minimum Ethereum balance is {} ETH, current account balance {} ETH'.format(
                Web3.fromWei(settings.MIN_SIGNUP_WEI_BALANCE, 'ether'),
                Web3.fromWei(eth_balance, 'ether')))
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


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serialize user data from database into JSON.
    """

    class Meta:
        model = User
        fields = ('ethereum_address', 'is_dormant', 'is_source_of_funds_verified', 'verification_status',)
        read_only_fields = fields

    verification_status = serializers.SerializerMethodField()

    def get_verification_status(self, obj):
        return obj.get_verbose_verification_status()