from .models import Utxo, Block

def get_block_body(nonce=None):
    mempool = Utxo.objects.filter(isMined=False)
    previous_block = Block.objects.last()
    previous_block_hash = previous_block.hash if previous_block else None
    return f'Mempool: {mempool.values()}, Previous_block_hash: {previous_block_hash}, Nonce: {nonce}'


