from django.urls import path
from . import views

urlpatterns= [
    path('create/', views.CreateTransaction.as_view(), 
         name='create_transaction'),
    path('create_block/', views.CreateBlock.as_view(),
         name='create_block')
]
