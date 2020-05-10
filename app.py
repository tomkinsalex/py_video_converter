from celery import Celery
from util import conf

app = Celery('app',
             broker='redis://%s:6379' % conf.REDIS_HOST,
             backend='redis://%s:6379' % conf.REDIS_HOST,
             include=['tasks.all'])

app.conf.task_routes = {
    '*.tasks': {'queue': conf.Q_ALL_HOSTS},
    '*.finish_up': {'queue': conf.Q_FINISH_UP}
}