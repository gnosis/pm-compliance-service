#!/bin/bash

set -euo pipefail

celery -A pm_compliance_service.taskapp worker -l INFO
