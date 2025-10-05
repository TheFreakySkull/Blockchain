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
        url = f'http://{node.ip}:{node.port}/transaction/create/'
        response = requests.post(url, json=validated_data)
        with open('output.txt', 'w') as file:
            file.write(response.text)

@shared_task
def send_block(validated_data):
    nodes = Node.objects.all()
    for node in nodes:
        url = f'http://{node.ip}:{node.port}/block/accept/'
        requests.post(url, json=validated_data)

@shared_task
def send_register_node(ip, port):
    data_dict = {'ip': settings.IP_ADDRESS,'port': settings.PORT}
    requests.post(f'http://{ip}:{port}/register_node/',
                  json=data_dict)

