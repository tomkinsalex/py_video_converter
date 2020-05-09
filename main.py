from util import conf
from manager.dir_watcher import DirWatcher
from multiprocessing import Process


def main():
    DirWatcher().run()

if __name__ == '__main__':
    main()