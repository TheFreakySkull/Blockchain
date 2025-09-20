from rest_framework.serializers import ModelSerializer
from rest_framework import serializers, exceptions, status
from .models import Transaction, Utxo
import hashlib

class OutputSerializer(ModelSerializer):
    class Meta:
        model = Utxo
        fields = ['recepient_pubkey', 'sender_pubkey', 'amount']
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
        inputs = validated_data['inputs'].filter(spent=False)
        outputs = validated_data['outputs']
        if inputs is None:
            raise exceptions.ValidationError({'inputs': 'inputs were already spent'}, code=status.HTTP_402_PAYMENT_REQUIRED)
        amount = 0
        for input in inputs:
            if input.recepient_pubkey == validated_data['sender_pubkey']:
                amount += input.amount
                continue
            raise exceptions.ValidationError({'input': 'dosent belong to sender'}, code=status.HTTP_403_FORBIDDEN)
        map(lambda x: amount - x.amount, outputs)
        if amount < 0:
            raise exceptions.ValidationError({'outputs': 'outputs amount more than inputs amount'}, code=status.HTTP_402_PAYMENT_REQUIRED)
        transaction_recipe = f'Inputs:{inputs.values('id')}, '\
                        f'Outputs:{outputs.values('recepient_pubkey, amount')}'\
                        f'Sender_pubkey: {validated_data['sender_pubkey']}'

        hash = hashlib.sha256(transaction_recipe).hexdigest()

        
        
        
