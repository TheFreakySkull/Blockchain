from django.contrib import admin
from . import models
#Register your models here.

@admin.register(models.Transaction)
class TrasactionAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Utxo)
class UtxoAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Block)
class BlockAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Node)
class NodeAdmin(admin.ModelAdmin):
    pass
