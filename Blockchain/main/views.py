from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models.aggregates import Sum

from .models import Transaction, Block, Utxo
from .serializers import TransactionSerializer, BlockSerializer, UtxoSerializer
from . import utils

class ListMempool(ListAPIView):
    queryset = Transaction.objects.filter(isMined=False)
    serializer_class = TransactionSerializer

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
        try:
            key = request.GET['pubkey']
        except MultiValueDictKeyError:
            return Response({'pubkey': 'pubkey is None'},
                            status=status.HTTP_400_BAD_REQUEST)

        utxos = Utxo.objects.filter(recepient_pubkey=key,
                                          spent=False)\
                                  .aggregate(utxo_amount=Sum('amount'))
        balance = utxos['utxo_amount']
        return Response({'balance': balance})

class GetChain(ListAPIView):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
