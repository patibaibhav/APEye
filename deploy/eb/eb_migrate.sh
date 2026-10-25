#!/bin/bash
# Runs Alembic migrations during an Elastic Beanstalk deployment (Amazon Linux 2023 Python platform).
# Invoked from .ebextensions/01_options.config with "bash eb_migrate.sh" so no executable bit is needed.
set -e
if [ -f /opt/elasticbeanstalk/deployment/env ]; then
  set -a
  . /opt/elasticbeanstalk/deployment/env
  set +a
fi
VENV_DIR=$(ls -d /var/app/venv/*/ | head -n 1)
. "${VENV_DIR}bin/activate"
cd "$(dirname "$0")"
alembic upgrade head
