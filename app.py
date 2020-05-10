from celery import Celery

app = Celery('app')

default_config = 'celery_config'
app.config_from_object(default_config)