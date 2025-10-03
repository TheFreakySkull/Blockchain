from .models import Transaction, Block
from .serializers import TransactionSerializer
import requests

def get_block_body(nonce=None):
    mempool = Transaction.objects.filter(isMined=False)
    serializer = TransactionSerializer(mempool, many=True)
    previous_block = Block.objects.latest('id')
    previous_block_hash = previous_block.hash if previous_block else None
    return f'Mempool: {serializer.data}, Previous_block_hash: {previous_block_hash}, Nonce: {nonce}'

def check_node(ip, port):
    url = f'http://{ip}:{port}/status/'
    response = requests.get(url)
    if response.status_code != 200 or response.json()['status'] != 'OK':
        return False
    return True

def send_transaction(validated_data):
    nodes = Node.objects.all()
    for node in nodes:
        url = f'http://{node['ip']}:{node['port']}/transactions/create/'
        requests.post(url, data=validated_data)

def send_block(validated_data):
    nodes = Node.objects.all()
    for node in nodes:
        url = f'http://{node['ip']}:{node['port']}/block/create/'
        requests.post(url, data=validated_data)
