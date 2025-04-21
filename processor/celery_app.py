import celery
from common import config
import os

# Either this, or -P eventlet to fix windows issue
#os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = celery.Celery('tasks', broker=config.redis_url)
app.conf.event_serializer = 'pickle'
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['application/json', 'application/x-python-serialize']

# Tasks import for celery to work
import worker.processor
