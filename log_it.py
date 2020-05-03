import logging

def get_logger(name):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    return logging.getLogger(name)

