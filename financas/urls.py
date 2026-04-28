from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('transacoes/', views.TransacaoListView.as_view(), name='transacao_list'),
    path('transacoes/nova/', views.TransacaoCreateView.as_view(), name='transacao_create'),
    path('transacoes/confirmar/<int:pk>/', views.transacao_confirmar, name='transacao_confirmar'),
    path('transacoes/excluir/<int:pk>/', views.transacao_excluir, name='transacao_excluir'),
    
    path('transferencia/nova/', views.transferencia_create, name='transferencia_create'),
    
    path('calendario/', views.calendario, name='calendario'),
    path('api/eventos/', views.transacao_eventos_json, name='transacao_eventos_json'),
    
    path('contas/', views.ContaListView.as_view(), name='conta_list'),
    path('contas/nova/', views.ContaCreateView.as_view(), name='conta_create'),
    
    path('metas/', views.MetaListView.as_view(), name='meta_list'),
    path('metas/nova/', views.MetaCreateView.as_view(), name='meta_create'),
    
    path('recorrencias/', views.RecorrenciaListView.as_view(), name='recorrencia_list'),
    path('recorrencias/nova/', views.RecorrenciaCreateView.as_view(), name='recorrencia_create'),
    
    path('importar/', views.importar_extrato, name='importar_extrato'),
    path('relatorio/pdf/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
    path('ajuda/', views.ajuda, name='ajuda'),
]
