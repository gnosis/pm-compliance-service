![Python 3.7](https://img.shields.io/badge/Python-3.7-blue.svg)
![Django 2](https://img.shields.io/badge/Django-2-blue.svg)

# Gnosis PM Compliance Service
Service for Gnosis Compliance

## Index of contents

- [Initial Configuration](#configuration)


Configuration
------------
Use `docker-compose` for running the project:

```bash
docker-compose build --force-rm
docker-compose up
```

Virtual enviroment
------------
You can choose to start developing the sight-operator service by running a local virtualenv.

1. Create the virtualenv: `virtualenv -p python3.7 venv`
2. Enable the virtualenv: `source venv/bin/activate`
3. Install libs: `pip install -r requirements.txt`
4. Run ganache locally or inside docker: `ganache -d`
5. Run initial migrations: `DJANGO_DOT_ENV_FILE=.env_test python manage.py migrate`

In order to get the whole system work, you need also to run a database and the Redis cache system. You can leverage docker-compose
for this purpose by running: `docker-compose up db redis`.
Take a look at `docker-compose.yml` file for the complete list of runnable services.

Configs
------------
There are 3 main configuration files:
1. .env_docker_compose, used by dockerized services (see docker-compose.yml)
2. .env_local, set to point to services running locally on your machine
3. .env_test, set to point to services running locally with specific test options.

If you wish to run tests or migrations or whatever django command, simply prepend
`DJANGO_DOT_ENV_FILE=config_file_to_use` env variable to the Django command.

Example of .env_test file:

```
AML_CLIENT_API_TOKEN=<YOUR TOKEN>
AML_CLIENT_BASE_URL=https://api.chainalysis.com/api/kyt/v1
AML_CLIENT_CLASS=pm_compliance_service.compliance.clients.chainalysis.Client
C_FORCE_ROOT=true
DEBUG=0
DJANGO_DEBUG=0
DJANGO_SETTINGS_MODULE=config.settings.test
DJANGO_SECRET_KEY=test-secret#-!key
DATABASE_URL=psql://postgres@localhost:5432/postgres
REDIS_URL=redis://localhost/0
CELERY_BROKER_URL=redis://localhost/0
ETHEREUM_NODE_URL=http://localhost:8545
ETHEREUM_TEST_PRIVATE_KEY=<YOUR KEY>
ENABLE_RECAPTCHA_VALIDATION=false
ONFIDO_API_REFERRER=https://gnosisdev.com
ONFIDO_API_TOKEN=<YOUR TOKEN>
PYTHONPATH=/app/pm_compliance_service
RECAPTCHA_SECRET_KEY=<YOUR KEY>
```

