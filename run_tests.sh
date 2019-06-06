#!/bin/bash

set -euo pipefail

docker-compose build --force-rm
docker-compose up --no-start db redis ganache
docker restart pm-compliance-service_db_1 pm-compliance-service_redis_1 pm-compliance-service_ganache_1
sleep 2
DJANGO_DOT_ENV_FILE=.env_local pytest
