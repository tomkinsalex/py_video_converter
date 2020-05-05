import logging
import conf
conf.init()

filename = conf.LOG_DIR+'/py_converter.log'
logging.basicConfig(filename=filename, filemode='+a',level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('requests').setLevel(logging.CRITICAL)

def get_logger(name):
    return logging.getLogger(name)

