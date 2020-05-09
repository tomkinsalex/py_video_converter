import subprocess
from util.log_it import get_logger
from os import listdir, walk, path
from os.path import isfile, join
from time import sleep
from util import conf,file_util
from PIL import Image
from util import conf
from celery import group, signature, Task
from app import app

logger = get_logger(__name__)


@app.task
def split(file_name, file_ext):
    logger.info("Starting to split video %s " % file_name)
    cmd_temp = """ffmpeg -fflags +genpts -i "{file_path}" -map 0 -c copy -f segment -segment_format {chunk_ext} -segment_time 120 -reset_timestamps 1 -v error "{chunk_prefix}{numbering}.{chunk_ext}" """
    cmd = cmd_temp.format(
        file_path=file_util.drop_zone_name(file_name,file_ext),
        chunk_ext=file_ext, 
        chunk_prefix=file_util.chunk_prefix(file_name,file_ext), 
        numbering="%02d")
    logger.info(" With command : %s" % cmd)
    run_shell(cmd)
    logger.info("Done splitting video %s " % file_name)
    num_chunks = int(run_shell_check_output('ls "%s"* | wc -l' % file_util.chunk_prefix(file_name,file_ext)))
    logger.info('Number of chunks created : %d' % num_chunks)
    return num_chunks


@app.task
def convert(counter, file_name, file_ext):
    cmd_temp = """ffmpeg -y -loglevel error -stats -i "{file_input}" -sn  -vcodec h264 -acodec libvorbis -preset fast -profile:v high -level 4.1 -crf 17 -pix_fmt yuv420p -max_muxing_queue_size 1024 "{file_output}" """
    logger.info("Starting to convert video chunk %d for %s" % (counter, file_name) )
    cmd = cmd_temp.format(
        file_input=file_util.chunk_name(file_name,file_ext,counter), 
        file_output=file_util.converting_name(file_name,counter))
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    logger.info("Done converting video chunk %d for %s" % (counter, file_name))
    cmd = """cp "%s" "%s" """ % (file_util.converting_name(file_name,counter), file_util.to_concat_name(file_name,counter))
    run_shell(cmd)
    cmd = """rm "%s" "%s" """ % (file_util.converting_name(file_name,counter), file_util.chunk_name(file_name,file_ext,counter))
    run_shell(cmd)
    logger.info("Copied file to concat dir")
    return file_util.to_concat_name(file_name,counter)


@app.task
def concat(input_files, file_name):
    input_files.sort()
    logger.info("Starting to concat video %s" % file_name)
    concat_list = file_util.concat_list(file_name)
    with open(concat_list, '+a') as f:
        f.write("ffconcat version 1.0\nfile '"+ "'\nfile '".join(input_files)+"'")
    cmd_temp = """ffmpeg -y -v error -safe 0 -i "{concat_list}" -map 0 -c copy "{output_file}" """
    cmd = cmd_temp.format(concat_list=concat_list, output_file=file_util.final_file_name(file_name))
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    logger.info("Done concating video %s" % file_name)
    cmd = """rm "%s" "%s" """ % (concat_list, '" "'.join(input_files))
    run_shell(cmd)
    logger.info("Done cleanup after concat")
    return file_util.final_file_name(file_name)

@app.task
def filebot(final_file,file_name, file_ext):
    cmd_temp= """filebot -script fn:amc --output "{final_dir}" --action  duplicate -non-strict "{final_file}" --log-file {filebot_log} --def excludeList="{processed_list}" --def artwork=y"""
    cmd = cmd_temp.format(
        final_dir=conf.FINAL_DIR, 
        final_file=final_file, 
        filebot_log=conf.FILEBOT_LOG_FILE, 
        processed_list=conf.FILEBOT_PROCESSED_LIST)
    logger.info("Starting organizer after vid %s" % final_file)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    run_shell('rm "%s"' % final_file)
    run_shell('rm "%s"' % file_util.drop_zone_name(file_name, file_ext))


@app.task
def assets_refresh():
    logger.info("Starting picture resizing")
    cmd = """rsync -r --exclude '*.mp4' --exclude '*.nfo' %s/ %s """ % (conf.FINAL_DIR, conf.ASSET_TMP_DIR)
    logger.info("Command used : %s" % cmd)
    run_shell(cmd)
    run_shell("rm -rf %s/*" % conf.ASSETS_DIR)
    run_shell("cp -r %s/* %s" % (conf.ASSET_TMP_DIR, conf.ASSETS_DIR))
    for (root, directories, filenames) in walk(conf.ASSETS_DIR):
        for filename in filenames:
            if ".png" in filename or ".jpg" in filename:
                image = Image.open(path.join(root,filename))
                if "clearart" in filename or "fanart" in filename:
                    image = image.resize([int(0.35 * s) for s in image.size])
                image.save(path.join(root,filename), quality=85, optimize=True)
    logger.info("Finished image resizing")
    


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
    if proc.returncode != 0:
        logger.error(stderr)
        raise ValueError(stderr)

    return stdout