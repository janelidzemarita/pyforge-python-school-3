from celery import Celery
from os import getenv

broker_url = getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
result_backend = getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery_app = Celery('tasks', broker=broker_url, backend=result_backend)
celery_app.conf.update(
    task_routes={
        'app.tasks.*': {'queue': 'default'},
    },
    broker_connection_retry_on_startup=True
)
