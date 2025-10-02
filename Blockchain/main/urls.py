from django.urls import path
from . import views

urlpatterns= [
    path('transactions/create/', views.CreateTransaction.as_view(), 
         name='transaction_create'),
    path('block/create/', views.CreateBlock.as_view(),
         name='block_create'),
    path('block/accept/', views.AcceptBlock.as_view(),
         name='block_accept')
]
