from util import conf
import sys
import time
from watchdog.observers import Observer
from manager.event_handler import EventHandler

class DirWatcher:
    def __init__(self, password):
        self.__src_path = conf.DROP_ZONE_DIR
        self.__event_handler = EventHandler(password)
        self.__event_observer = Observer()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        self.__schedule()
        self.__event_observer.start()

    def stop(self):
        self.__event_observer.stop()
        self.__event_observer.join()

    def __schedule(self):
        self.__event_observer.schedule(
            self.__event_handler,
            self.__src_path,
            recursive=True
        )