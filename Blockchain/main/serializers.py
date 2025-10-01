from rest_framework.serializers import ModelSerializer
from rest_framework import serializers, exceptions, status
from django.db.models import Count, Sum
import hashlib
import ecdsa

from .models import Transaction, Utxo


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
    inputs = serializers.PrimaryKeyRelatedField(many=True,
                    queryset=Utxo.objects.filter(spent=False, isMined=True))
    
    class Meta: 
        model = Transaction
        fields = ['inputs', 'outputs', 'sender_pubkey', 'recepient_pubkey', 'signature']
    
    def get_transacton_hash(self, inputs_ids, output_data, sender_pubkey_data):
        transaction_recipe = f'Inputs:{inputs_ids}, '\
                    f'Outputs:{[(output['recepient_pubkey'], output['amount']) for output in output_data]} '\
                    f'Sender_pubkey: {sender_pubkey_data}'
        hash = hashlib.sha256(transaction_recipe.encode()).hexdigest()

        with open('output.txt', 'w') as file:
            file.write(hash)
        return hash

    def validate_transaction(self, validated_data, inputs_ids, outputs_data, sender_pubkey_data):
        inputs = Utxo.objects.filter(id__in=inputs_ids, spent=False)\
                             .aggregate(inputs_amount=Sum('amount'),
                                        inputs_count=Count('id'))

        if len(inputs_ids) != inputs['inputs_count']:
            raise exceptions.ValidationError({'inputs': 'inputs were already'\
                                             ' spent or does\'nt'\
                                             ' belong to sender'}, 
                                    code=status.HTTP_402_PAYMENT_REQUIRED)
        
        outputs_amount = sum(output['amount'] for output in outputs_data)
        if inputs['inputs_amount'] - outputs_amount < 0:
            raise exceptions.ValidationError({'outputs': 'outputs amount more'\
                                              ' than inputs amount'},
                                        code=status.HTTP_402_PAYMENT_REQUIRED)

        hash = self.get_transacton_hash(inputs_ids, outputs_data, sender_pubkey_data)
        sender_pubkey_bytes = bytes.fromhex(sender_pubkey_data)
        vk = ecdsa.VerifyingKey.from_string(sender_pubkey_bytes,
                                            curve=ecdsa.SECP256k1,
                                            hashfunc=hashlib.sha256,
                                            validate_point=True)
        signature_bytes = bytes.fromhex(validated_data['signature'])
        
        try:
            vk.verify(signature_bytes, hash.encode(), sigdecode=ecdsa.util.sigdecode_der)
            with open('output.txt', 'a') as file:
                file.write(f'{file} succes')

        except ecdsa.BadSignatureError:
            raise exceptions.ValidationError({'signature': 'signature is not '\
                                              'valid'},
                                              code=status.HTTP_403_FORBIDDEN)
        return True

    def create(self, validated_data):
        inputs_data = validated_data.pop('inputs')
        outputs_data = validated_data.pop('outputs')
        sender_pubkey_data = validated_data.pop('sender_pubkey')
        inputs_ids = [input.id for input in inputs_data]
        self.validate_transaction(validated_data, inputs_ids, outputs_data, sender_pubkey_data)
        
        hash = self.get_transacton_hash(inputs_ids, outputs_data, sender_pubkey_data)
        transaction = Transaction.objects.create(**validated_data, hash=hash)
        inputs = Utxo.objects.filter(id__in=inputs_ids).update(spent=True)
        transaction.inputs.add(inputs)
        outputs = Utxo.objects.bulk_create(
            [Utxo(**output, sender_pubkey=sender_pubkey_data) for output in outputs_data]
        )
        transaction.outputs.set(outputs)
        return transaction
