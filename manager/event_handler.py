from util.log_it import get_logger
from watchdog.events import RegexMatchingEventHandler
from manager.task_runner import execute_flow
from multiprocessing import Process

logger = get_logger(__name__)

class EventHandler(RegexMatchingEventHandler):
    VIDEO_REGEX = [r"^.*\.?(mkv|mp4|mpeg|m4v|flv|avi)$"]

    def __init__(self):
        super().__init__(self.VIDEO_REGEX)
        

    def on_created(self, event):
        if event.src_path.split("/")[-1][0] != ".":
            print(event.src_path)
            proc = Process(target=execute_flow, args=(event.src_path,),daemon=True)
            proc.start()
            logger.info("Started new proc for %s" % event.src_path)
