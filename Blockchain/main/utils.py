import requests
import ecdsa
import hashlib
import json
from django.conf import settings
from .models import Transaction, Block, Node, Utxo
from .serializers import TransactionSerializer
from . import exceptions

def get_block_body(transactions, previous_block_hash, nonce=None, miner_pubkey='x'):
    return f'Mempool: {transactions}, Previous_block_hash: {previous_block_hash},'\
           f' Nonce: {nonce}, Miner_pubkey: {miner_pubkey}'

def get_block_hash(transactions, miner_pubkey, previous_block_hash,
                   nonce):
    body = get_block_body(nonce, miner_pubkey, transactions,
                          previous_block_hash)
    hash = hashlib.sha256(body.encode()).hexdigest()
    return hash

def check_block_nonce(*args):
    hash = get_block_hash(*args)
    if hash[:settings.POW_ZEROS_AMOUNT] != '0' * settings.POW_ZEROS_AMOUNT:
        return False
    return True

def mempool_not_empty():
    return Transaction.objects.filter(isMined=False).exists()

def get_transacton_hash(inputs_ids, output_data, sender_pubkey_data):
        transaction_recipe = f'Inputs:{inputs_ids}, '\
                    f'Outputs:{[(output['recepient_pubkey'], output['amount']) \
                    for output in output_data]}, '\
                    f'Sender_pubkey: {sender_pubkey_data}'
        with open('hash.txt', 'w') as f:
            f.write(transaction_recipe)

        hash = hashlib.sha256(transaction_recipe.encode()).hexdigest()
        return hash

def validate_transaction_signature(inputs_ids, outputs_data,
                                   sender_pubkey_data, signature,
                                   ):
    hash = get_transacton_hash(inputs_ids, outputs_data, sender_pubkey_data)
    sender_pubkey_bytes = bytes.fromhex(sender_pubkey_data)
    vk = ecdsa.VerifyingKey.from_string(sender_pubkey_bytes,
                                            curve=ecdsa.SECP256k1,
                                            hashfunc=hashlib.sha256,
                                            validate_point=True)
    signature_bytes = bytes.fromhex(signature)
        
    try:
        vk.verify(signature_bytes, hash.encode(), sigdecode=ecdsa.util.sigdecode_der)
            
    except ecdsa.BadSignatureError:
        return False
    return True

def find_valid_chains(block_hash):
    nodes = Node.objects.all()
    proper_chains = []
    for node in nodes:
        response = requests.get(f'http://{node.ip}/chain/')
        data = json.loads(response.text)
        hashes = [block.hash for block in data]
        if block_hash in hashes:
            proper_chains += data['results']
    return proper_chains

def validate_chain(chain, excluded_inputs=None):
    spent_utxo_hashes = []
    for block in chain:
        for transaction in block['transactions']:
            for input in transaction['inputs']:
                if input['hash'] not in spent_utxo_hashes:
                    if input['hash'] in excluded_inputs:
                        spent_utxo_hashes += input['hash']
                        continue
                    try:
                        spent_model_utxo = Utxo.objects.get(hash=input['hash']).filter(spent=True)
                    except Utxo.DoesNotExist:
                        spent_model_utxo = None

                    if not spent_model_utxo:
                        spent_utxo_hashes += input['hash']
                        continue
                return False
    
            if sum([input['amount'] for input in transaction['inputs']]) < \
               sum([output['amount'] for output in transaction['outputs']]):
                return False

            inputs_ids = [input['id'] for input in transaction['inputs']]
            if not validate_transaction_signature(inputs_ids,
                                                  transaction['outputs'],
                                                  transaction['sender_pubkey'],
                                                  transaction['signature']):
                return False

        if not check_block_nonce(block['transactions'], block['miner_pubkey'], 
                                 block['previous_block_hash'], block['nonce']):
            return False
        return True

def replace_chain_part(new_part, wrong_part):
    wrong_part.delete()
    for block in new_part:
        new_block = Block.objects.create(id=block['id'],
                        hash=block['hash'],
                        time_stamp=block['time_stamp'],
                        previous_block_hash=block['previous_block_hash'],
                        nonce=block['nonce'])

        for transaction in block['transactions']:
            new_transaction = Transaction.objects.create(
                                block=new_block,
                                sender_pubkey=transaction['sender_pubkey'],
                                signature=transaction['signature'],
                                time_stamp=transaction['time_stamp'],
                                hash=transaction['hash'],
                                generated=transaction['generated'],
                                isMined=transaction['isMined'])

            for output in transaction['outputs']:
                Utxo.objects.create(
                    input_transaction=output['input_transaction'],
                    output_transaction=new_transaction,
                    recepient_pubkey=output['recepient_pubkey'],
                    sender_pubkey=output['sender_pubkey'],
                    amount=output['amount'], spent=output['spent'],
                    isMined=output['isMined'], hash=output['hash']
                )
            Utxo.objects.filter(hash__in=[input['hash'] \
                for input in transaction['inputs']]).update(
                input_transaction=transaction)

def fix_chain(block_hash):
    proper_chains = find_valid_chains(block_hash)
    if proper_chains is None:
        raise exceptions.ChainNotFound('Blockchain with given previous block hash was not found'\
                                       'within known nodes')
    blocks_hashes = Block.objects.all()[:50].values_list('hash', flat=True)
    conflict_chain = [block for block in proper_chains\
                        if block['hash'] not in blocks_hashes]
    unvalid_chain = Block.objects.exclude(hash__in=[block.hash for block in proper_chains])

    if len(unvalid_chain) > len(conflict_chain):
        raise exceptions.ChainLengthError('Length of given chain'\
                                     ' less then current one')

    unvalid_inputs_hashes = Utxo.objects.filter(input_transaction__block__in=unvalid_chain)


    if not validate_chain(conflict_chain, unvalid_inputs_hashes):
        raise exceptions.ChainValidationError('The given chain is not valid')

    replace_chain_part(conflict_chain, unvalid_chain)
    

