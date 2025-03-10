import logging
from sys import platform

def get_logger(name):
    logger = logging.getLogger(name)
    if platform == 'linux':
        from systemd.journal import JournaldLogHandler
        journald_handler = JournaldLogHandler()
        journald_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(journald_handler)
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.INFO)
    return logger

