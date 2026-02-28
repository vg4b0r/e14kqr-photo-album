#!/bin/bash
set -e

cd /var/app/current
source /var/app/venv/*/bin/activate

export FLASK_APP=app
flask db upgrade