from django.urls import path
from . import views

urlpatterns= [
    path('transactions/create/', views.CreateTransaction.as_view(), 
         name='transaction_create'),
    path('block/create/', views.CreateBlock.as_view(),
         name='block_create'),
    path('block/accept/', views.AcceptBlock.as_view(),
         name='block_accept'),
    path('balance/', views.CountBalance.as_view(),
         name='balance_count'),
    path('chain/', views.GetChain.as_view(),
         name='chain_get'),
    path('mempool/', views.ListMempool.as_view(),
         name='mempool'),
    path('status/', views.Status.as_view(),
         name='status'),
    path('register_node/', views.RegisterNode.as_view(),
         name='register_node')
]
