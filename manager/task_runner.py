from os import path
from time import sleep,time
from util import conf
from tasks.all import split, convert, map_task, concat, filebot, assets_refresh
from util.log_it import get_logger
from util import file_util
from  hurry.filesize import size

from celery import signature, chain, group, chord

logger = get_logger(__name__)


def execute_flow(file_path):
    file_size = wait_until_copied(file_path)
    file_name, file_ext = file_util.split_file_name(file_path)

    if conf.STATS == "Y":
        with_stats(file_name,file_ext,file_size)
    else:
        routine = ( split.s(file_name,file_ext).set(queue=conf.Q_PIS) |
                    map_task.s(convert.s(file_name,file_ext)).set(queue=conf.Q_ALL_HOSTS) |
                    concat.s(file_name,file_ext).set(queue=conf.Q_PIS) |
                    filebot.si(file_name,file_ext).set(queue=conf.Q_PIS) | 
                    assets_refresh.si(file_name,file_ext).set(queue=conf.Q_PIS))
        task = routine.apply_async()
        task.wait()


def with_stats(file_name,file_ext,file_size):
    
    start_time = time()
    
    num_chunks = split_task(file_name,file_ext)
    split_done = time()

    num_range = convert_task(file_name,file_ext,num_chunks)
    convert_done = time()

    concat_task(file_name, num_range)
    concat_done = time()

    organize_tasks(file_name,file_ext)
    organize_done = time()

    save_results({
        'name' : file_name,
        'ext' : file_ext,
        'size' : str(size(file_size)),
        'num_chunks': str(num_chunks),
        'split' : str(split_done - start_time),
        'convert': str(convert_done - split_done),
        'concat' : str(concat_done - convert_done),
        'organize': str(organize_done - concat_done),
        'all': str(organize_done - start_time) 
    })


def split_task(file_name, file_ext):
    logger.info("Starting split task for %s " % file_name)
    task = split.apply_async(args=(file_name,file_ext), queue=conf.Q_PIS)
    task.wait(timeout=None, interval=2)
    num_chunks = task.get()
    return num_chunks


def convert_task(file_name, file_ext, num_chunks):
    logger.info("Starting converting routine for %s" % file_name)
    routine = group(convert.s(counter=i,file_name=file_name,file_ext=file_ext) for i in range(num_chunks))
    task = routine()
    num_range = task.get()
    logger.info("Finished converting routine for %s" % file_name)
    return num_range


def concat_task(file_name, num_range):
    logger.info("Starting concat task for %s " % file_name)
    task = concat.apply_async(args=(num_range,file_name), queue=conf.Q_PIS)
    task.wait(timeout=None, interval=5)
    logger.info("Finished concat task for %s" % file_name)


def organize_tasks(file_name,file_ext):
    logger.info("Starting organize routine for %s" % file_name)
    organize_routine = ( filebot.si(args=(file_name,file_ext)).set(queue=conf.Q_PIS) | assets_refresh.si(args=()).set(queue=conf.Q_PIS) )
    task_organize = organize_routine.apply_async(args=())
    task_organize.wait(timeout=None, interval=5)
    logger.info("Finished organize routine for %s" % file_name)


def wait_until_copied(file_path):
    logger.info("Waiting for file to finish copying")
    file_size = -1
    while True:
        if file_size == path.getsize(file_path) and file_size > 100000000:
            break
        file_size = path.getsize(file_path)
        sleep(3)
    logger.info("Done waiting, file size: %d " % file_size)
    logger.info("Processing new video file event for %s" % file_path)
    sleep(5)
    return file_size


def save_results(result_dict):
    with open(conf.RESULT_CSV_FILE, 'a') as f:
        file_line = ','.join(result_dict.values())
        f.write('%s\n' % file_line)
