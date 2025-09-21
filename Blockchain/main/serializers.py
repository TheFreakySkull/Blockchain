from rest_framework.serializers import ModelSerializer
from rest_framework import serializers, exceptions, status
from .models import Transaction, Utxo
from django.db.model import Count
import hashlib
import ecdsa

class OutputSerializer(ModelSerializer):
    class Meta:
        model = Utxo
        fields = ['id','recepient_pubkey', 'sender_pubkey', 'amount']
        read_only_fields = ['sender_pubkey']

class InputSerializer(ModelSerializer):
    class Meta:
        model = Utxo
        fields = ['id','recepient_pubkey', 'sender_pubkey', 'amount']
        read_only_fields = ['recepient_pubkey', 'sender_pubkey', 'amount']


class TransactionSerializer(ModelSerializer):
    outputs = OutputSerializer(many=True)
    inputs = InputSerializer(many=True)
    
    class Meta: 
        fields = ['inputs', 'outputs', 'sender_pubkey', 'recepient_pubkey', 'signature']

    def create(self, validated_data):
        inputs = validated_data['inputs'].filter(spent=False, 
                                                 recepient_pubkey=validated_data['sender_pubkey'])\
                                         .aggregate(inputs_amount=Count('amount'))
        outputs = validated_data['outputs'].aggregate(outputs_amount=Count('amount'))
        if inputs is None:
            raise exceptions.ValidationError({'inputs': 'inputs were already spent or does\'nt'\
                                              'belong to sender'}, code=status.HTTP_402_PAYMENT_REQUIRED)

        if inputs.inputs_amount - outputs.outputs_amount < 0:
            raise exceptions.ValidationError({'outputs': 'outputs amount more than inputs amount'},
                                             code=status.HTTP_402_PAYMENT_REQUIRED)

        transaction_recipe = f'Inputs:{inputs.values('id')}, '\
                        f'Outputs:{outputs.values('recepient_pubkey, amount')}'\
                        f'Sender_pubkey: {validated_data['sender_pubkey']}'

        hash = hashlib.sha256(transaction_recipe).hexdigest()
        sender_pubkey_bytes = bytes.fromhex(validated_data['sender_pubkey'])
        vk = ecdsa.VerifyingKey.from_string(sender_pubkey_bytes, curve=ecdsa.SECP256k1,
                                            hashfunc=hashlib.sha256)
        try:
            vk.verify(validated_data['signature'],hash)
        except ecdsa.BadSignatureError:
            raise exceptions.ValidationError({'signature': 'signature is not valid'},
                                             code=status.HTTP_403_FORBIDDEN)

        transaction = Transaction.objects.create(**validated_data, hash=hash)
        for input in validated_data['inputs']:
            utxo = Utxo.objects.get(input).update(spent=True)
            transaction.inputs.add(utxo)

        for output in validated_data['outputs']:
            utxo = Utxo.objects.create(**output,
                                sender_pubkey=validated_data['sender_pubkey'])
            transaction.outputs.add(utxo)

        
        




