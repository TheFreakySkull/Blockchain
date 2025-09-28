from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .models import Transaction
from .serializers import TransactionSerializer

class CreateTransaction(CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
