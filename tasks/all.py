import subprocess
import json
import urllib.request
from util.log_it import get_logger
from os import listdir, walk, path
from glob import iglob
from os.path import isfile, join
from time import sleep
from util import conf,file_util
from util.exceptions import ShellException
from PIL import Image
from util import conf
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
    logger.info('Starting group convert')
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
        cmd = """rm "%s" "%s" """ % (concat_list, '" "'.join(input_files))
        run_shell(cmd)
        logger.info("Done cleanup after concat")
    except ShellException as ex:
        logger.exception(ex)
        self.retry(throw=True, queue=conf.Q_PIS, routing_key=conf.Q_PIS+'.retry')


@app.task(name='task.filebot')
def filebot(file_name, file_ext):
    final_file = file_util.final_file_name(file_name)
    cmd_temp= """filebot -script fn:amc --output "{final_dir}" --action  duplicate -non-strict "{final_file}" --def excludeList="{processed_list}" --def artwork=y --def minLengthMS=0 --def minFileSize=0"""
    cmd = cmd_temp.format(
        final_dir=conf.FINAL_DIR, 
        final_file=final_file, 
        filebot_log=conf.FILEBOT_LOG_FILE, 
        processed_list=conf.FILEBOT_PROCESSED_LIST)
    logger.info("Starting organizer after vid %s" % final_file)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    sleep(2)
    run_shell('rm "%s" "%s"' % (final_file,file_util.drop_zone_name(file_name, file_ext)))
    logger.info("Finished filebot for %s " % file_name)


@app.task(name='task.assets_refresh')
def assets_refresh(file_name, file_ext):
    logger.info("Starting picture resizing")
    cmd = """rsync -r --exclude '*.mp4' --exclude '*.nfo' %s/ %s """ % (conf.FINAL_DIR, conf.ASSET_TMP_DIR)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    cmd = """rsync -r --exclude '*.mp4' --exclude '*.nfo' --exclude '*.jpg' --exclude '*.png' %s/ %s """ % (conf.FINAL_DIR, conf.ASSETS_DIR)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    with open(conf.PROCESSED_PICS_LOG, 'r') as f:
        processed = { line.strip() for line in f.readlines() }
    newly_processed = []
    for (root, directories, filenames) in walk(conf.ASSET_TMP_DIR):
        asset_root = root.replace(conf.ASSET_TMP_DIR, conf.ASSETS_DIR)
        platform_agnostic_root = root.replace(conf.ASSET_TMP_DIR, '')
        for filename in filenames:
            ext = filename.split('.')[-1]
            if "png" == ext or "jpg" == ext:
                if not path.join(platform_agnostic_root,filename) in processed:
                    newly_processed.append(path.join(platform_agnostic_root,filename))
                    logger.info("New image to optimize %s" % path.join(platform_agnostic_root,filename))
                    image = Image.open(path.join(root,filename))
                    if "clearart" in filename or "fanart" in filename:
                        image = image.resize([int(0.32 * s) for s in image.size])
                    image.save(path.join(asset_root,filename), quality=82, optimize=True)
    if newly_processed:
        with open(conf.PROCESSED_PICS_LOG, 'a') as f:
            for processed_pic in newly_processed:
                f.write('%s\n' % processed_pic)
    logger.info("Finished image resizing, processed %d new images" % len(newly_processed))
    return max(iglob('%s/**/*.mp4' % conf.FINAL_DIR, recursive=True), key=path.getctime)


@app.task(name='task.post_new_video')
def post_new_video(video_path):
    logger.info("About to post video with path %s" % video_path)
    body = { 'path' : video_path }
    req = urllib.request.Request(conf.API_POST_URL)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    logger.info("Response: " % response.read())


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