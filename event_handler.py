from log_it import get_logger
from watchdog.events import RegexMatchingEventHandler
from job_producer import JobProducer
from multiprocessing import Process

logger = get_logger(__name__)

class EventHandler(RegexMatchingEventHandler):
    VIDEO_REGEX = [r"^.*\.?(mkv|mp4|mpeg|m4v|flv|avi)$"]

    def __init__(self, convert_q, organize_q):
        super().__init__(self.VIDEO_REGEX)
        self.convert_q = convert_q
        self.organize_q = organize_q
        

    def on_created(self, event):
        if event.src_path.split("/")[-1][0] != ".":
            job_p = JobProducer(self.convert_q, self.organize_q)
            proc = Process(target=job_p.process, args=(event.src_path,),daemon=True)
            proc.start()
            logger.info("Started new proc for %s" % event.src_path)
