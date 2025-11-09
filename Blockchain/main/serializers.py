from rest_framework.serializers import ModelSerializer
from rest_framework.exceptions import ValidationError
from rest_framework import serializers, status
from django.db.models import Count, Sum
from django.conf import settings
import hashlib
import ecdsa

from . import tasks
from . import exceptions
from .models import Node, Transaction, Utxo, Block

class UtxoSerializer(ModelSerializer):
    class Meta:
        model = Utxo
        fields = ['id','recepient_pubkey', 'sender_pubkey', 'amount',
                  'hash', 'spent']
        read_only_fields = ['sender_pubkey', 'hash']

class InputSerializer(UtxoSerializer):
    id = serializers.IntegerField(required=False)
    class Meta(UtxoSerializer.Meta):
        read_only_fields = [
            'recepient_pubkey', 'sender_pubkey', 'amount']

class TransactionSerializer(ModelSerializer):
    outputs = UtxoSerializer(many=True)
    inputs = InputSerializer(many=True)

    class Meta: 
        model = Transaction
        fields = ['id', 'inputs', 'outputs', 'sender_pubkey', 'signature']
    
    def validate_transaction(self, validated_data, inputs_ids, outputs_data, sender_pubkey_data):

        inputs = Utxo.objects.filter(id__in=inputs_ids, spent=False,
                                    recepient_pubkey=sender_pubkey_data, isMined=True)\
                             .aggregate(inputs_amount=Sum('amount'),
                                        inputs_count=Count('id'))

        if len(inputs_ids) != inputs['inputs_count']:
            raise ValidationError({'inputs': 'inputs were already'\
                                             ' spent or does\'nt'\
                                             ' belong to sender'}, 
                                    code=status.HTTP_402_PAYMENT_REQUIRED)
        
        outputs_amount = sum(output['amount'] for output in outputs_data)
        if inputs['inputs_amount'] - outputs_amount < 0:
            raise ValidationError({'outputs': 'outputs amount more'\
                                              ' than inputs amount'},
                                        code=status.HTTP_402_PAYMENT_REQUIRED)

        from . import utils
        if not utils.validate_transaction_signature(inputs_ids, outputs_data,
                                                    sender_pubkey_data, 
                                                    validated_data['signature']):
            raise ValidationError({'signature': 'signature is not '\
                                              'valid'},
                                              code=status.HTTP_403_FORBIDDEN)
        return True

    def create(self, validated_data):
        inputs_data = validated_data.pop('inputs')
        outputs_data = validated_data.pop('outputs')
        sender_pubkey_data = validated_data.pop('sender_pubkey')
        inputs_ids = [input['id'] for input in inputs_data]
        self.validate_transaction(validated_data, inputs_ids,
                                  outputs_data, sender_pubkey_data)
        
        from . import utils
        hash = utils.get_transacton_hash(inputs_ids, outputs_data, sender_pubkey_data)
        transaction = Transaction.objects.create(
            **validated_data,
            sender_pubkey=sender_pubkey_data,
            hash=hash)
        Utxo.objects.filter(id__in=inputs_ids).update(input_transaction=transaction, spent=True)
        utxo_objects = [
            Utxo(
                **output,
                sender_pubkey=sender_pubkey_data,
                output_transaction=transaction
            ) for output in outputs_data
        ]

        utxos = Utxo.objects.bulk_create(utxo_objects)
        map(lambda x: x.save(), utxos)

        # tasks.send_transaction.delay({'inputs': inputs_data,
        #                               'outputs': outputs_data,
        #                               'sender_pubkey': sender_pubkey_data,
        #                               'signature': validated_data.pop(
        #                                                 'signature')})
        return transaction

class IdTransactionSerializer(TransactionSerializer):
    class Meta(TransactionSerializer.Meta):
        fields = ['id', 'hash']

class BlockSerializer(ModelSerializer):
    miner_pubkey = serializers.CharField(max_length=250, write_only=True)
    previous_block_hash = serializers.CharField(max_length=250)
    # hash = serializers.CharField(max_length=250)
    time_stamp = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S',
                                           read_only=True)
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = [
            'hash', 
            'time_stamp'
        ]

    def validate_block(self, validated_data, transactions):
        validated_data = validated_data.copy()
        previous_block_hash = validated_data.pop('previous_block_hash')
        previous_block_hash = None if previous_block_hash == 'None'\
                                else previous_block_hash
        certain_block = Block.objects.last()
        certain_block_hash = certain_block.hash if certain_block else None
        if previous_block_hash != certain_block_hash:
            from . import utils
            try:
                utils.fix_chain(previous_block_hash)
            except exceptions.ChainLengthError as e:
                raise ValidationError({'error': 'Block is not valid, a shorter fork was found',
                                       'detail': e.message}, code=status.HTTP_400_BAD_REQUEST)
            except exceptions.ChainValidationError as e:
                raise ValidationError({'error': 'Block is not valid, fork was found but not valid',
                                       'detail': e.message}, code=status.HTTP_400_BAD_REQUEST)
            except exceptions.ChainNotFound as e:
                raise ValidationError({'error': 'Block is not valid, fork was not found',
                                       'detail': e.message}, code=status.HTTP_400_BAD_REQUEST)



            if transactions is None:
                raise ValidationError({'transactions': 'transactions not given or not valid'},
                                  code=status.HTTP_400_BAD_REQUEST)
        nonce = validated_data.pop('nonce')
        miner_pubkey = validated_data.pop('miner_pubkey')
        from . import utils

        if not utils.check_block_nonce(transactions, miner_pubkey, 
                                       previous_block_hash, nonce):
            raise ValidationError({'nonce': 'nonce does not valid or expired'},
                                  code=status.HTTP_400_BAD_REQUEST)

    def create(self, validated_data):
        from . import utils
        if not utils.mempool_not_empty():
            raise ValidationError({'detail': 'Mempool is empty,'\
                                     ' wait until next transaction.'},
                                   code=status.HTTP_400_BAD_REQUEST)
        transactions_data = validated_data['transactions']
        transactions = Transaction.objects.filter(
                    # id__in=[transaction['id'] for transaction in transactions_data],
                    hash__in=[transaction['hash'] for transaction in transactions_data]
                    # signature__in=[transaction['signature'] for transaction in transactions_data]
        )

        self.validate_block(validated_data, transactions)
        # with open('hash.txt', 'w') as f:
        #      f.write(str(validated_data))
        miner_pubkey = validated_data.pop('miner_pubkey')
        miner_transaction = Transaction.objects.create(
            sender_pubkey='system',
            signature='system',
            generated=True,
            hash=hashlib.sha256('system'.encode()).hexdigest(),
            isMined=True
        )

        Utxo.objects.create(
            sender_pubkey='system',
            recepient_pubkey=miner_pubkey,
            amount=settings.MINER_FEE_AMOUNT,
            isMined=True,
            input_transaction=miner_transaction
        )
        
        nonce = validated_data['nonce']
        last_block = Block.objects.last()
        previous_block_hash = last_block.hash if last_block else None
        
        block_hash = utils.get_block_hash(
            transactions, miner_pubkey,
            previous_block_hash,
            nonce
        )

        block = Block.objects.create(hash=block_hash,
                previous_block_hash=previous_block_hash, nonce=nonce,
                miner_pubkey=miner_pubkey)
        transactions.update(block=block, isMined=True)
        tasks.send_block.delay(validated_data)
        return block

class NodeSerializer(ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'
        read_only_fields = ['id']
    
    def create(self, validated_data):
        check_node = tasks.check_node.delay(**validated_data)
        if not check_node:
            raise ValidationError({'node': 'node is not valid'},
                                   code=status.HTTP_400_BAD_REQUEST)
        tasks.send_register_node.delay(validated_data)
        return super().create(validated_data)
