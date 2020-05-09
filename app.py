from celery import Celery
from util import conf

app = Celery('app',
             broker='redis://%s:6379' % conf.REDIS_HOST,
             backend='redis://%s:6379' % conf.REDIS_HOST,
             include=['tasks.all'])