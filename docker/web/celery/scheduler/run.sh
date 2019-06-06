#!/bin/bash

set -euo pipefail

# DEBUG set in .env
if [ ${DEBUG:-0} = 1 ]; then
    log_level="debug"
else
    log_level="info"
fi

echo "==> Running Celery beat <=="
exec celery beat -A pm_compliance_service.taskapp -S django_celery_beat.schedulers:DatabaseScheduler --loglevel $log_level
