import subprocess
from log_it import get_logger
from os import listdir
from os import walk
from os import path
from os.path import isfile, join
from time import sleep
import conf

logger = get_logger(__name__)

def split_vid(vid_name, chunk_prefix, chunk_suffix):
    logger.info("Starting to split video %s " % vid_name)
    cmd_temp = """ffmpeg -fflags +genpts -i "{vid_name}" -map 0 -c copy -f segment -segment_format {chunk_suffix} -segment_time 300 -reset_timestamps 1 -v error "{chunk_prefix}{numbering}.{chunk_suffix}" """
    cmd = cmd_temp.format(vid_name=vid_name, chunk_suffix=chunk_suffix, chunk_prefix=chunk_prefix, numbering="%02d")
    logger.info(" With command : %s" % cmd)
    run_shell(cmd)
    logger.info("Done splitting video %s " % vid_name)

def convert_vid(video_name, video_output):
    cmd_temp = """ffmpeg -y -loglevel error -stats -i "{video_name}" -sn  -vcodec h264 -acodec libvorbis -preset fast -profile:v high -level 4.1 -crf 17 -pix_fmt yuv420p -max_muxing_queue_size 1024 "{video_output}" """
    logger.info("Starting to convert video %s" % video_name )
    cmd = cmd_temp.format(video_name=video_name, video_output=video_output)
    logger.info("Command used : %s" % cmd)
    if run_shell(cmd): 
        logger.info("Done converting video %s" % video_output)
        cmd = """cp "%s" %s""" % (video_output, conf.TO_CONCAT_DIR)
        run_shell(cmd)
        cmd = """rm "%s" "%s" """ % (video_output, video_name)
        run_shell(cmd)
        logger.info("Copied file to concat dir")
    else:
        raise ValueError("Conversion failed")
    


def waiting_for_vids(output_vids):
    logger.info("Starting to wait for videos")
    expected_vids = [vid.split('/')[-1] for vid in output_vids]
    while True:
        files = [f for f in listdir(conf.TO_CONCAT_DIR) if isfile(join(conf.TO_CONCAT_DIR, f))]
        if all(elem in files for elem in expected_vids):
            logger.info("Found all videos")
            break
        logger.info("to_concat files :")
        logger.info(",".join(files))
        logger.info("expected files :")
        logger.info(",".join(expected_vids))
        logger.info("Still waiting ...")
        sleep(20)


def concat_vids(input_vids, output_file, file_prefix):
    logger.info("Starting to concat video %s" % file_prefix)
    concat_list = "%s/%s.txt" % (conf.TO_CONCAT_DIR, file_prefix)
    with open(concat_list, '+a') as f:
        f.write("ffconcat version 1.0\nfile '"+ "'\nfile '".join(input_vids)+"'")
    cmd_temp = """ffmpeg -y -v error -safe 0 -i "{input_str}" -map 0 -c copy "{output_file}" """
    cmd = cmd_temp.format(input_str=concat_list, output_file=output_file)
    logger.info("Command used : %s" % cmd)
    if run_shell(cmd):
        logger.info("Done concating video %s" % file_prefix)
        cmd = """rm "%s" "%s" """ % (concat_list, '" "'.join(input_vids))
        run_shell(cmd)
        logger.info("Done cleanup after concat")
    else:
        raise ValueError("Concat failed")

def organize_vids(input_file, final_output_file):
    from PIL import Image
    cmd_temp= """filebot -script fn:amc --output "{final_dir}" --action  duplicate -non-strict "{final_file}" --log-file {filebot_log} --def excludeList="{processed_list}" --def artwork=y"""
    cmd = cmd_temp.format(final_dir=conf.FINAL_DIR, final_file=final_output_file, filebot_log=conf.FILEBOT_LOG_FILE, processed_list=conf.FILEBOT_PROCESSED_LIST)
    logger.info("Starting organizer after vid %s" % final_output_file)
    logger.info("Command used : %s" % cmd)
    if run_shell(cmd):
        run_shell('rm "%s"' % final_output_file)
        logger.info("Starting picture organizer")
        cmd = """rsync -r --exclude={'*.mp4','*.nfo'} %s/ %s """ % (conf.FINAL_DIR, conf.ASSET_TMP_DIR)
        logger.info("Command used : %s" % cmd)
        if run_shell(cmd):
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
            run_shell('rm "%s" ' % input_file)


def run_shell(cmd):
    proc = subprocess.Popen(cmd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        shell=True
    )
    stdout, stderr = proc.communicate()
 
    if proc.returncode != 0:
        logger.error(stderr)
        return False
    else:
        logger.info(stdout)
        return True