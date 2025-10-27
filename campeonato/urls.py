from django.urls import path
from . import views  

urlpatterns = [
    path('', views.tabela_classificacao, name='tabela-classificacao'),
    
    path(
        'rodada/<int:rodada_num>/', 
        views.tabela_classificacao, 
        name='tabela-classificacao-rodada'
    ),
    
    path(
        'time/<int:time_id>/', 
        views.detalhes_time, 
        name='detalhes-time'
    ),
]

