from util.log_it import get_logger
from watchdog.events import RegexMatchingEventHandler
from manager.producer import process
from multiprocessing import Process

logger = get_logger(__name__)

class EventHandler(RegexMatchingEventHandler):
    VIDEO_REGEX = [r"^.*\.?(mkv|mp4|mpeg|m4v|flv|avi)$"]

    def __init__(self):
        super().__init__(self.VIDEO_REGEX)
        

    def on_created(self, event):
        if event.src_path.split("/")[-1][0] != ".":
            proc = Process(target=process, args=(event.src_path,),daemon=True)
            proc.start()
            #process(event.src_path)
            logger.info("Started new proc for %s" % event.src_path)
