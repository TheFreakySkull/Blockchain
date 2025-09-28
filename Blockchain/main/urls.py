from django.urls import path
from . import views

urlpatterns= [
    path('create/', views.CreateTransaction.as_view(), 
         name='create_transaction')
]
