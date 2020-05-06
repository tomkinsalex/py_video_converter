#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath "$0")")
. "$SCRIPT_PATH/env/bin/activate"
python $SCRIPT_PATH/main.py --start_who manager --redis_host localhost