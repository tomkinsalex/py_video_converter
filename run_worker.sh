#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath "$0")")
. "$SCRIPT_PATH/env/bin/activate"
python $SCRIPT_PATH/main.py --start_who worker --worker_type convert --redis_host 10.0.0.1