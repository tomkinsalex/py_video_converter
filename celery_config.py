from util import conf
from kombu import Queue

broker_url = 'redis://%s:6379' % conf.REDIS_HOST
result_backend = 'redis://%s:6379' % conf.REDIS_HOST

imports = ('tasks.all')

task_default_queue = conf.Q_ALL_HOSTS
task_queues = (
    Queue(conf.Q_ALL_HOSTS, routing_key=conf.Q_ALL_HOSTS+'.#'),
    Queue(conf.Q_FINISH_UP, routing_key=conf.Q_FINISH_UP+'.#'),
    Queue(conf.Q_PIS, routing_key=conf.Q_PIS+'.#'),
)
task_default_exchange = 'tasks'
task_default_exchange_type = 'topic'
task_default_routing_key = conf.Q_ALL_HOSTS+'.default'

task_routes = {
        'tasks.all.split': {
            'queue': conf.Q_ALL_HOSTS,
            'routing_key': conf.Q_ALL_HOSTS+'.default',
        },
        'tasks.all.convert': {
            'queue': conf.Q_ALL_HOSTS,
            'routing_key': conf.Q_ALL_HOSTS+'.default',
        },
        'tasks.all.concat': {
            'queue': conf.Q_ALL_HOSTS,
            'routing_key': conf.Q_ALL_HOSTS+'.default',
        },
        'tasks.all.filebot': {
            'queue': conf.Q_FINISH_UP,
            'routing_key': conf.Q_FINISH_UP+'.default',
        },
        'tasks.all.assets_refresh': {
            'queue': conf.Q_FINISH_UP,
            'routing_key': conf.Q_FINISH_UP+'.default',
        },
}