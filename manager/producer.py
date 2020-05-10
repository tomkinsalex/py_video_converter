from os import path
from time import sleep
from util import conf
from tasks.all import split, convert, concat, filebot, assets_refresh
from util.log_it import get_logger
from util import file_util

from celery import signature, chain, group, chord

logger = get_logger(__name__)


def process(file_path):
    logger.info("Waiting for file to finish copying")
    file_size = -1
    while True:
        if file_size == path.getsize(file_path) and file_size > 100000000:
            break
        file_size = path.getsize(file_path)
        sleep(3)
    logger.info("Done waiting, file size: %d " % file_size)
    logger.info("Processing new video file event for %s" % file_path)
    sleep(3)
    produce_jobs(file_path)


def produce_jobs(file_path):
    file_name, file_ext = file_util.split_file_name(file_path)
    logger.info("Starting split task for %s " % file_name)
    split_task = split.apply_async((file_name,file_ext),queue=conf.Q_ALL_HOSTS)
    split_task.wait(timeout=None, interval=1)
    num_chunks = split_task.get()
    routine = ( group(convert.s((i,file_name,file_ext), queue=conf.Q_ALL_HOSTS) for i in range(num_chunks)) | concat.s((file_name), queue=conf.Q_ALL_HOSTS) | filebot.si((file_name,file_ext), queue=conf.Q_FINISH_UP) | assets_refresh.si((), queue=conf.Q_FINISH_UP))
    logger.info("Starting routine for %s" % file_name)
    task = routine.apply_async()
    task.wait(timeout=None, interval=5)
    logger.info("Finished processing routine for %s" %file_name)






