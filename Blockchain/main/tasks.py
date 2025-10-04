import requests

from celery import shared_task
from django.conf import settings
from .models import Node

@shared_task
def check_node(ip, port):
    url = f'http://{ip}:{port}/status/'
    response = requests.get(url)
    if response.status_code != 200 or response.json()['status'] != 'OK':
        return False
    return True

@shared_task
def send_transaction(validated_data):
    nodes = Node.objects.all()
    for node in nodes:
        url = f'http://{node['ip']}:{node['port']}/transactions/create/'
        requests.post(url, data=validated_data)

@shared_task
def send_block(validated_data):
    nodes = Node.objects.all()
    for node in nodes:
        url = f'http://{node['ip']}:{node['port']}/block/create/'
        requests.post(url, data=validated_data)

@shared_task
def send_register_node(ip, port):
    requests.post(f'http://{ip}:{port}/register_node/',
                  data=[settings.IP_ADDRESS, settings.PORT])

