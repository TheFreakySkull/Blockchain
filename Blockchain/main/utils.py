from .models import Transaction, Block
from .serializers import TransactionSerializer

def get_block_body(nonce=None, miner_pubkey='x'):
    mempool = Transaction.objects.filter(isMined=False)
    serializer = TransactionSerializer(mempool, many=True)
    previous_block = Block.objects.latest('id')
    previous_block_hash = previous_block.hash if previous_block else None
    return f'Mempool: {serializer.data}, Previous_block_hash: {previous_block_hash}, Nonce: {nonce}, Miner_pubkey: {miner_pubkey}'


