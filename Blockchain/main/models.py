from django.db import models
from django.utils.ipv6 import MAX_IPV6_ADDRESS_LENGTH


class Utxo(models.Model):
    recepient_pubkey = models.CharField(max_length=256)
    sender_pubkey = models.CharField(max_length=256)
    amount = models.PositiveIntegerField()
    spent = models.BooleanField(default=False)
    isMined = models.BooleanField(default=False)

class Transaction(models.Model):
    inputs = models.ManyToManyField(Utxo, related_name='input_transactions')
    outputs = models.ManyToManyField(Utxo, related_name='output_transactions')
    sender_pubkey = models.CharField(max_length=250)
    recepient_pubkey = models.CharField(max_length=250)
    signature = models.CharField(max_length=256)
    time_stamp = models.DateTimeField(auto_now_add=True)
    hash = models.CharField(max_length=256)
    generated = models.BooleanField(default=False)
    isMined = models.BooleanField(default=False)

class Block(models.Model):
    transactions = models.ManyToManyField(Transaction)
    hash = models.CharField(max_length=256)
    previous_block_hash = models.CharField(max_length=256, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    nonce = models.PositiveIntegerField()


class Node(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    port = models.PositiveIntegerField()
    

