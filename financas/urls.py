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
    path('contas/editar/<int:pk>/', views.ContaUpdateView.as_view(), name='conta_update'),
    path('contas/excluir/<int:pk>/', views.ContaDeleteView.as_view(), name='conta_delete'),

    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nova/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/editar/<int:pk>/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/excluir/<int:pk>/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),

    path('membros/', views.MembroListView.as_view(), name='membro_list'),
    path('membros/novo/', views.MembroCreateView.as_view(), name='membro_create'),
    path('membros/editar/<int:pk>/', views.MembroUpdateView.as_view(), name='membro_update'),
    path('membros/excluir/<int:pk>/', views.MembroDeleteView.as_view(), name='membro_delete'),

    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/nova/', views.TagCreateView.as_view(), name='tag_create'),
    path('tags/editar/<int:pk>/', views.TagUpdateView.as_view(), name='tag_update'),
    path('tags/excluir/<int:pk>/', views.TagDeleteView.as_view(), name='tag_delete'),
    
    path('metas/', views.MetaListView.as_view(), name='meta_list'),
    path('metas/nova/', views.MetaCreateView.as_view(), name='meta_create'),
    path('metas/editar/<int:pk>/', views.MetaUpdateView.as_view(), name='meta_update'),
    path('metas/excluir/<int:pk>/', views.MetaDeleteView.as_view(), name='meta_delete'),
    
    path('orcamentos/', views.OrcamentoListView.as_view(), name='orcamento_list'),
    path('orcamentos/novo/', views.OrcamentoCreateView.as_view(), name='orcamento_create'),
    
    path('relatorios/', views.RelatorioListView.as_view(), name='relatorio_list'),
    path('relatorios/novo/', views.RelatorioCreateView.as_view(), name='relatorio_create'),
    path('relatorios/ia/<int:pk>/', views.gerar_relatorio_ia, name='gerar_relatorio_ia'),
    
    path('recorrencias/', views.RecorrenciaListView.as_view(), name='recorrencia_list'),
    path('recorrencias/nova/', views.RecorrenciaCreateView.as_view(), name='recorrencia_create'),
    
    path('importar/', views.importar_extrato, name='importar_extrato'),
    path('relatorio/pdf/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
    path('ajuda/', views.ajuda, name='ajuda'),
]
