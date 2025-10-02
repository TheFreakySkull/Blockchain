from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models.aggregates import Sum

from .models import Transaction, Block, Utxo
from .serializers import TransactionSerializer, BlockSerializer, UtxoSerializer
from . import utils

class ListMempool(ListAPIView):
    queryset = Utxo.objects.filter(isMined=False)
    serializer_class = UtxoSerializer

class CreateTransaction(CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

class AcceptBlock(CreateAPIView):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer

class CreateBlock(APIView):
    def get(self, request):
        return Response({'Block': utils.get_block_body('x')})


class CountBalance(APIView):
    def get(self, request):
        key = request.GET['pubkey']
        if key is None:
            return Response({'pubkey': 'pubkey is None'},
                            status=status.HTTP_400_BAD_REQUEST)

        input_utxos = Utxo.objects.filter(recepient_pubkey=key)\
                                  .aggregate(inputs_amount=Sum('amount'))
        output_utxos = Utxo.objects.filter(sender_pubkey=key)\
                                   .aggregate(outputs_amount=Sum('amount'))
        balance = input_utxos['inputs_amount'] - output_utxos['outputs_amount']
        return Response({'balance': f'{balance} utxo'})

