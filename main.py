import argparse
import conf
from worker import start_worker

def main(redis_host, start_who, worker_type):
    redis_host = redis_host.strip('"')
    conf.init()
    if start_who ==  'worker':
        start_worker(redis_host,conf.REDIS_PORT, worker_type)
    else:
        from threading import Thread
        from manager import start_manager

        thread_producer = Thread(target=start_manager, args=(redis_host,conf.REDIS_PORT,))
        thread_producer.daemon = True
        thread_producer.start()

        thread_splitter = Thread(target=start_worker, args=(redis_host,conf.REDIS_PORT,'splitter',))
        thread_splitter.daemon = True
        thread_splitter.start()

        start_worker(redis_host,conf.REDIS_PORT, 'organizer')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Main for starting and stopping managers and workers")
    parser.add_argument('--redis_host', dest='redis_host', help='Address of redis host', required=True)
    parser.add_argument('--start_who', dest='start_who', help='Start manager or worker', required=True, choices=['manager', 'worker'])
    parser.add_argument('--worker_type', dest='worker_type', help='Converter or organizer worker', required=False, choices=['convert', 'organize','split'])

    args = parser.parse_args()
    start_who = args.start_who
    worker_type = args.worker_type
    redis_host = args.redis_host
    print(start_who)
    main(redis_host,start_who, worker_type)