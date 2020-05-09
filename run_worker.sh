#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath "$0")")
. "$SCRIPT_PATH/env/bin/activate"
cd "$SCRIPT_PATH"
celery -A app worker -c 4