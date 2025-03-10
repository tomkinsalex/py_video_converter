import subprocess
import util.content_api_util as content_api
from util.log_it import get_logger
from os import path
from glob import glob
from time import sleep
from util import conf,file_util
from util.exceptions import ShellException
from celery import group, signature, chord
from celery.task import subtask
from app import app

logger = get_logger(__name__)


@app.task(name='task.split', bind=True, max_retries=3)
def split(self, file_name, file_ext):
    try:
        logger.info("Starting to split video %s " % file_name)
        cmd_temp = """ffmpeg -fflags +genpts -i "{file_path}" -map 0 -c copy -f segment -segment_format {chunk_ext} -segment_time 120 -reset_timestamps 1 -v error "{chunk_prefix}{numbering}.{chunk_ext}" """
        cmd = cmd_temp.format(
            file_path=file_util.drop_zone_name(file_name,file_ext),
            chunk_ext=file_ext, 
            chunk_prefix=file_util.chunk_prefix(file_name,file_ext), 
            numbering="%02d")
        logger.info(" With command : %s" % cmd)
        run_shell(cmd)
        sleep(2)
        logger.info("Done splitting video %s " % file_name)
        num_chunks = int(run_shell_check_output('ls "%s"* | wc -l' % file_util.chunk_prefix(file_name,file_ext)))
        logger.info('Number of chunks created : %d' % num_chunks)
        return num_chunks
    except ShellException as ex:
        logger.exception(ex)
        self.retry(throw=True, queue=conf.Q_PIS, routing_key=conf.Q_PIS+'.retry')


@app.task(name='task.map_task')
def map_task(num_repeat, task_sig, on_complete):
    logger.info('Starting %d map tasks' % num_repeat)
    task_sig = subtask(task_sig)
    task_group = group(task_sig.clone(args=(i,)) for i in range(num_repeat))
    return chord(task_group)(subtask(on_complete))


@app.task(name='task.convert', bind=True, max_retries=3)
def convert(self, counter, file_name, file_ext):
    try:
        cmd_temp = """ffmpeg -y -loglevel error -stats -i "{file_input}" -sn  -vcodec h264 -acodec libvorbis -preset fast -profile:v high -level 4.1 -crf 17 -pix_fmt yuv420p -max_muxing_queue_size 1024 "{file_output}" """
        logger.info("Starting to convert video chunk %d for %s" % (counter, file_name) )
        cmd = cmd_temp.format(
            file_input=file_util.chunk_name(file_name,file_ext,counter), 
            file_output=file_util.converting_name(file_name,counter))
        logger.info("Command used : %s" % cmd)
        run_shell(cmd)
        sleep(2)
        logger.info("Done converting video chunk %d for %s" % (counter, file_name))
        cmd = """cp "%s" "%s" """ % (file_util.converting_name(file_name,counter), file_util.to_concat_name(file_name,counter))
        run_shell(cmd)
        sleep(2)
        cmd = """rm "%s" "%s" """ % (file_util.converting_name(file_name,counter), file_util.chunk_name(file_name,file_ext,counter))
        run_shell(cmd)
        logger.info("Copied file to concat dir")
        return counter
    except ShellException as ex:
        logger.exception(ex)
        self.retry(throw=True, queue=conf.Q_PIS, routing_key=conf.Q_PIS+'.retry')


@app.task(name='task.concat', bind=True, max_retries=3)
def concat(self, num_range, file_name,file_ext):
    try:
        num_range.sort()
        input_files = [file_util.to_concat_name(file_name,num) for num in num_range]
        logger.info("Starting to concat video %s" % file_name)
        concat_list = file_util.concat_list(file_name)
        with open(concat_list, 'w+') as f:
            print("ffconcat version 1.0", file=f)
            for chunk in input_files:
                print("file '%s'" % chunk, file=f)
        cmd_temp = """ffmpeg -y -v error -safe 0 -i "{concat_list}" -map 0 -c copy "{output_file}" """
        cmd = cmd_temp.format(concat_list=concat_list, output_file=file_util.final_file_name(file_name))
        logger.info("Command used : %s" % cmd)
        run_shell(cmd)
        sleep(2)
        logger.info("Done concating video %s" % file_name)
        cmd = """rm "%s" """ % ('" "'.join(input_files))
        #cmd = """rm "%s" "%s" """ % (concat_list, '" "'.join(input_files))
        run_shell(cmd)
        logger.info("Done cleanup after concat")
    except ShellException as ex:
        logger.exception(ex)
        self.retry(throw=True, queue=conf.Q_PIS, routing_key=conf.Q_PIS+'.retry')


@app.task(name='task.filebot')
def filebot(file_name, file_ext):
    final_file = file_util.final_file_name(file_name)
    cmd_temp= """filebot -script fn:amc --output "{final_dir}" --action  duplicate -non-strict "{final_file}" --def artwork=y --def minLengthMS=0 --def minFileSize=0"""
    cmd = cmd_temp.format(
        final_dir=conf.FINAL_DIR, 
        final_file=final_file, 
        filebot_log=conf.FILEBOT_LOG_FILE)
    logger.info("Starting organizer after vid %s" % final_file)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    sleep(2)
    #run_shell('rm "%s" "%s"' % (final_file,file_util.drop_zone_name(file_name, file_ext)))
    run_shell('rm "%s"' % (final_file))
    logger.info("Finished filebot for %s " % file_name)
    return max(glob('%s/**/*.mp4' % conf.FINAL_DIR, recursive=True), key=path.getctime)


@app.task(name='task.assets_refresh')
def assets_refresh(new_video, file_name, file_ext):
    if content_api.is_new_content(new_video):
        from util import image_util
        logger.info("New Content - Starting picture resizing")
        cmd = """rsync -r --exclude "/*/*/*/" --exclude '*.mp4' --exclude '*.nfo' %s/ %s """ % (conf.FINAL_DIR, conf.ASSET_TMP_DIR)
        logger.info("Command used : %s" % cmd)
        run_shell(cmd)
        cmd = """rsync -r --exclude "/*/*/*/" --exclude '*.mp4' --exclude '*.nfo' --exclude '*.jpg' --exclude '*.png' %s/ %s """ % (conf.FINAL_DIR, conf.ASSETS_DIR)
        logger.info("Command used : %s" % cmd)
        run_shell(cmd)
        content_root = file_util.content_root_dir(new_video)
        image_util.process_images(content_root)
        logger.info("Finished image resizing, processed new images")
    return new_video


@app.task(name='task.post_new_video')
def post_new_video(video_path):
    logger.info("About to post video with path %s" % video_path)
    content_api.post_new_video(video_path)


def check_lengths(new_video, file_name, file_ext):
    logger.info("Checking lengths for %s" % file_name)
    cmd_template = """ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}" """
    new_length = run_shell_check_output(cmd_template.format(file_path=new_video))
    old_length = run_shell_check_output(cmd_template.format(file_path=file_util.drop_zone_name(file_name, file_ext)))
    logger.info("New length: %s" % new_length)
    logger.info("Old length: %s" % old_length)
    return float(old_length), float(new_length)


def clean_up(file_name, file_ext):
    run_shell('rm "%s"' % (file_util.drop_zone_name(file_name, file_ext)))
    run_shell( """rm "%s" """ % (file_util.concat_list(file_name)))


def to_investigate(file_name, file_ext):
    run_shell('mv "%s" %s' % (file_util.drop_zone_name(file_name, file_ext), conf.TO_INVESTIGATE_DIR))
    run_shell( """mv "%s" %s """ % (file_util.concat_list(file_name),conf.TO_INVESTIGATE_DIR))


def run_shell(cmd):
    call_subprocess(cmd)


def run_shell_check_output(cmd):
    stdout = call_subprocess(cmd)
    return stdout.decode().strip()


def call_subprocess(cmd):
    proc = subprocess.Popen(cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell=True
    )
    stdout, stderr = proc.communicate()
    if "filebot" in cmd and proc.returncode == 100:
        return stdout

    if proc.returncode != 0:
        raise ShellException(cmd, stdout, stderr)

    return stdout