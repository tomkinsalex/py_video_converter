from rq import Connection, Worker
from redis import Redis
import job_service
import subprocess

from log_it import get_logger

logger = get_logger(__name__)

def start_worker(host, port, worker_type):
   with Connection(connection=Redis(host=host, port=port)):
        worker = Worker('%s_q' % worker_type )
        worker.work()
