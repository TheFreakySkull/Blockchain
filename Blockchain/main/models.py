from django.db import models
from django.utils.ipv6 import MAX_IPV6_ADDRESS_LENGTH

class Block(models.Model):
    hash = models.CharField(max_length=256)
    previous_block_hash = models.CharField(max_length=256)
    time_stamp = models.DateTimeField(auto_now_add=True)
    nonce = models.PositiveIntegerField()

class Transaction(models.Model):
    inputs = models.ManyToManyField(Utxo, )
    outputs = models.ManyToManyField(Utxo)
    sender_pubkey = models.CharField(max_legth=50)
    recepient_pubkey = models.CharField(max_legth=50)
    signature = models.CharField(max_length=256)
    time_stamp = models.DateTimeFIeld(auto_now_add=True)
    hash = models.CharField(max_length=256)
    isMined = models.BooleanField(default=False)

class Utxo(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    recipient_pubkey = models.CharField(max_length=256)
    sender_pubkey = models.CharField(max_length=256)
    amount = models.PositiveIntegerField()

