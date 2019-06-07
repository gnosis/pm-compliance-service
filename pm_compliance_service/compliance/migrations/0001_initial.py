# Generated by Django 2.2.2 on 2019-06-06 21:05

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import gnosis.eth.django.models
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=45)),
                ('iso2', models.CharField(max_length=2, primary_key=True, serialize=False)),
                ('iso3', models.CharField(max_length=3)),
                ('numeric', models.PositiveSmallIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('ethereum_address', gnosis.eth.django.models.EthereumAddressField(unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('cra', models.PositiveSmallIntegerField()),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'PENDING'), (1, 'FROZEN'), (2, 'FAILED'), (3, 'VERIFIED'), (4, 'ONBOARDING')])),
                ('is_source_of_funds_verified', models.BooleanField(default=False)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='country_users', to='compliance.Country')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]