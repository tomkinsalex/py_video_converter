#!/bin/bash

SCRIPT_PATH=$(dirname "$(realpath "$0")")
. "$SCRIPT_PATH/env/bin/activate"
cd "$SCRIPT_PATH"
celery -A app multi $1 w_all_hosts w_pis -Q:w_all_hosts q_all_hosts -c:w_all_hosts 2 -Q:w_pis q_pis -c:w_pis 1 --pidfile=/var/tmp/%n.pid --logfile=/var/tmp/%n.log