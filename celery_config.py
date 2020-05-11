from util import conf
from kombu import Queue

broker_url = 'redis://%s:6379' % conf.REDIS_HOST
result_backend = 'redis://%s:6379' % conf.REDIS_HOST

imports = ('tasks.all')

task_default_queue = conf.Q_ALL_HOSTS
task_queues = (
    Queue(conf.Q_ALL_HOSTS, routing_key=conf.Q_ALL_HOSTS+'.#'),
    Queue(conf.Q_PIS, routing_key=conf.Q_PIS+'.#'),
)
task_default_exchange = 'tasks'
task_default_exchange_type = 'topic'
task_default_routing_key = conf.Q_ALL_HOSTS+'.default'

q_pis_dict = {'queue': conf.Q_PIS, 'routing_key': conf.Q_PIS+'.default'}
q_all_dict = {'queue': conf.Q_ALL_HOSTS, 'routing_key': conf.Q_ALL_HOSTS+'.default'}

task_routes = {
        'tasks.all.split': q_pis_dict,
        'tasks.all.convert': q_all_dict,
        'tasks.all.concat': q_all_dict,
        'tasks.all.filebot': q_pis_dict,
        'tasks.all.assets_refresh': q_pis_dict,
}

task_acks_late = True

worker_prefetch_multiplier = 1

task_track_started = True