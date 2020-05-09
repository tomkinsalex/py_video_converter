import logging
from systemd.journal import JournaldLogHandler

def get_logger(name):
    logger = logging.getLogger(name)
    journald_handler = JournaldLogHandler()
    journald_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(journald_handler)
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    return logger

