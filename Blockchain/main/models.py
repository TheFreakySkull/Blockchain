import hashlib
from django.db import models

class Block(models.Model):
    hash = models.CharField(max_length=256)
    previous_block_hash = models.CharField(max_length=256, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    nonce = models.PositiveIntegerField()


class Transaction(models.Model):
    block = models.ForeignKey(Block, null=True, on_delete=models.CASCADE)
    sender_pubkey = models.CharField(max_length=250)
    signature = models.CharField(max_length=256)
    time_stamp = models.DateTimeField(auto_now_add=True)
    hash = models.CharField(max_length=256)
    generated = models.BooleanField(default=False)
    isMined = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.block:
            self.isMined = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Transaction {self.id} {self.time_stamp}'

class Utxo(models.Model):
    input_transaction = models.ForeignKey(Transaction, 
                                          on_delete=models.SET_NULL,
                                          null=True,
                                          related_name='inputs')
    output_transaction = models.ForeignKey(Transaction, 
                                          on_delete=models.CASCADE,
                                          null=True,
                                          related_name='outputs')
    recepient_pubkey = models.CharField(max_length=256)
    sender_pubkey = models.CharField(max_length=256)
    amount = models.PositiveIntegerField()
    spent = models.BooleanField(default=False)
    isMined = models.BooleanField(default=False)
    hash = models.CharField(null=True)
    
    def save(self, *args, **kwargs):
        hash = hashlib.sha256(f'{self.recepient_pubkey} {self.sender_pubkey}'\
               f' {self.amount}'.encode()).hexdigest()
        self.hash = hash

        if self.input_transaction is not None:
            self.spent = True
        super().save(*args, **kwargs)


class Node(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    port = models.PositiveIntegerField()
    
    class Meta:
        indexes = [
            models.Index(fields=['ip'])
        ]

