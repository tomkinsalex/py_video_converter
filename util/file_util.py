from util import conf
from os import rename

OUTPUT_EXT='.mp4'

def chunk_name(file_name, file_ext, counter):
    return chunk_prefix(file_name, file_ext) + "{:0>2d}".format(counter) + '.' + file_ext


def chunk_prefix(file_name, file_ext):
    return conf.CHUNKED_DIR +'/'+file_name


def converting_name(file_name,counter):
    return conf.CONVERTING_DIR + '/' +file_name + "{:0>2d}".format(counter) + OUTPUT_EXT


def to_concat_name(file_name,counter):
    return conf.TO_CONCAT_DIR + '/' +file_name + "{:0>2d}".format(counter) + OUTPUT_EXT


def drop_zone_name(file_name,file_ext):
    return conf.DROP_ZONE_DIR + '/' + file_name + '.' + file_ext


def final_file_name(file_name):
    return conf.FILEBOT_DIR + '/' + file_name + OUTPUT_EXT


def concat_list(file_name):
    return conf.TO_CONCAT_DIR + '/' + file_name +'.txt'


def split_file_name(file_path):
    file_name = '.'.join(file_path.split('.')[:-1]).split('/')[-1]
    file_ext = file_path.split('.')[-1]
    if "'" in file_name or '"' in file_name:
        file_name = file_name.replace("'","")
        file_name = file_name.replace('"','')
        rename(file_path, drop_zone_name(file_name, file_ext))
    return file_name, file_ext