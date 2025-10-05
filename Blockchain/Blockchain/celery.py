import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Blockchain.settings')

app = Celery('Blockchain',
             broker=f'amqp://{settings.RABBITMQ_USER}'\
             f':{settings.RABBITMQ_PASSWORD}'\
             '@localhost:5672/')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
