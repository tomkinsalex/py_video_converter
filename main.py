from util import conf
from manager.dir_watcher import DirWatcher
from multiprocessing import Process
from manager import test_concat


def main():
    DirWatcher().run()

if __name__ == '__main__':
    #main()
    test_concat.test()