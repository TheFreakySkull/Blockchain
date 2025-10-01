from django.http import JsonResponse
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import View
from rest_framework.response import Response
from rest_framework import status

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

class CreateBlock(View):
    def get(self, request):
        return JsonResponse({'Block': utils.get_block_body('x')})
        
