from util import conf
from manager.dir_watcher import DirWatcher
from multiprocessing import Process
from tasks.all import post_new_video
import os
from glob import glob
import sys

def main(password):
    DirWatcher(password).run()


def post_all_vids():
    for f in glob('%s/**/*.mp4' % conf.FINAL_DIR, recursive=True):
        post_new_video(f)

if __name__ == '__main__':
    
    if sys.argv[1] == 'Y':
         post_all_vids()
    else:
        main(sys.argv[2])