from util import conf
from os import rename
import re

OUTPUT_EXT='mp4'
SHOW_DIR = "/TV Shows/"
MOVIE_DIR = "/Movies/"

def chunk_name(file_name, file_ext, counter):
    return "{}{:0>2d}.{}".format(chunk_prefix(file_name, file_ext),counter,file_ext)


def chunk_prefix(file_name, file_ext):
    return '%s/%s' % (conf.CHUNKED_DIR,file_name)


def converting_name(file_name,counter):
    return "{}/{}{:0>2d}.{}".format(conf.CONVERTING_DIR,file_name,counter,OUTPUT_EXT)


def to_concat_name(file_name,counter):
    return "{}/{}{:0>2d}.{}".format(conf.TO_CONCAT_DIR,file_name,counter,OUTPUT_EXT)


def drop_zone_name(file_name,file_ext):
    return '%s/%s.%s' % (conf.DROP_ZONE_DIR, file_name, file_ext)


def final_file_name(file_name):
    return '%s/%s.%s' % (conf.FILEBOT_DIR, file_name, OUTPUT_EXT)


def concat_list(file_name):
    return '%s/%s.txt' % (conf.TO_CONCAT_DIR, file_name)


def content_root_dir(new_video_path):
    drop_right = -2 if SHOW_DIR in new_video_path else -1
    return '/'.join(new_video_path.split('/')[:drop_right])


def split_file_name(file_path):
    file_name = '.'.join(file_path.split('.')[:-1]).split('/')[-1]
    file_ext = file_path.split('.')[-1]
    new_name = re.sub('[^A-Za-z0-9\-\_\.\s]+','', file_name)
    if new_name != file_name:
        rename(file_path, drop_zone_name(new_name, file_ext))
    return new_name, file_ext