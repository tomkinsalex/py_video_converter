from os import path
from time import sleep,time
from util import conf
from tasks.all import split, convert, map_task, concat, filebot, assets_refresh, post_new_video, check_lengths, to_investigate, clean_up
from util.log_it import get_logger
from util import file_util
from  hurry.filesize import size
from glob import glob

from celery import signature, chain, group, chord

logger = get_logger(__name__)


def execute_flow(file_path, password):
    file_size = wait_until_copied(file_path)
    file_name, file_ext = file_util.split_file_name(file_path)

    if conf.STATS == "Y":
        with_stats(file_name,file_ext,file_size, password)
    else:
        args = (file_name,file_ext)
        routine = ( split.s(*args).set(queue=conf.Q_PIS) |
                    map_task.s(
                    task_sig=convert.s(*args).set(queue=conf.Q_ALL_HOSTS),
                    on_complete=( 
                    concat.s(*args).set(queue=conf.Q_PIS) |
                    filebot.si(*args).set(queue=conf.Q_PIS) | 
                    assets_refresh.si(*args).set(queue=conf.Q_PIS) |
                    post_new_video.s().set(queue=conf.Q_PIS)
                    )))
        routine.apply_async()

def send_email(file_name, file_ext, password):
    import smtplib, ssl
    port = 465
    context = ssl.create_default_context()
    sender_email = "wfb7cap4ba@gmail.com"
    to_email = "alexctomkins@gmail.com"
    message = """Subject: Converting failure for %s \nThis message is sent from Python.""" % (file_name)
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, message)


def with_stats(file_name,file_ext,file_size, password):
    
    start_time = time()
    
    num_chunks = split_task(file_name,file_ext)
    split_done = time()

    num_range = convert_task(file_name,file_ext,num_chunks)
    convert_done = time()

    concat_task(file_name, file_ext, num_range)
    concat_done = time()

    organize_tasks(file_name,file_ext)
    organize_done = time()

    posting_task()
    
    old_length , new_length = check_lengths(file_name,file_ext)
    if abs(old_length - new_length) > 20:
        to_investigate(file_name,file_ext)
        send_email(file_name,file_ext, password)
    else:
        clean_up(file_name,file_ext)

    save_results({
        'name' : file_name,
        'ext' : file_ext,
        'size' : str(size(file_size)),
        'old_length' : str(old_length),
        'new_length' : str(new_length),
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


def concat_task(file_name, file_ext, num_range):
    logger.info("Starting concat task for %s " % file_name)
    task = concat.apply_async(args=(num_range,file_name,file_ext), queue=conf.Q_PIS)
    task.wait(timeout=None, interval=5)
    logger.info("Finished concat task for %s" % file_name)


def organize_tasks(file_name,file_ext):
    logger.info("Starting organize routine for %s" % file_name)
    organize_routine = ( filebot.si(file_name,file_ext).set(queue=conf.Q_PIS) | assets_refresh.si(file_name,file_ext).set(queue=conf.Q_PIS) )
    task_organize = organize_routine.apply_async()
    task_organize.wait(timeout=None, interval=5)
    logger.info("Finished organize routine for %s" % file_name)


def posting_task():
    video_path = max(glob('%s/**/*.mp4' % conf.FINAL_DIR, recursive=True), key=path.getctime)
    post_new_video(video_path)


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
