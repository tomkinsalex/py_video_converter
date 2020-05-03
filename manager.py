import threading
import video_dir_watcher
import os

from redis import Redis
from rq import Queue
from log_it import get_logger

    
def start_manager(host, port):    
    logger = get_logger(__name__)
    convert_q = Queue(connection=Redis(host=host, port=port),name="convert_q")
    organize_q = Queue(connection=Redis(host=host, port=port),name="organize_q")
    splitter_q = Queue(connection=Redis(host=host, port=port),name="split_q")
    logger.info('Server started at %s on port %s' % (host, port))
    video_dir_watcher.VideoDirWatcher(convert_q, organize_q, splitter_q).run()
