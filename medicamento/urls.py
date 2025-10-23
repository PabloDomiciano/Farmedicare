from django.urls import path

from medicamento.views import (
    MedicamentoCreateView, 
    MedicamentoListView,
    MedicamentoUpdateView,
    MedicamentoDeleteView,
    EntradaMedicamentoCreateView, 
    EntradaMedicamentoListView, 
    EntradaMedicamentoDeleteView, 
    EntradaMedicamentoUpdateView,
    MedicamentoEstoqueListView,
    NotificacoesListView,
    NotificacoesAPIView,
)

urlpatterns = [
    path('cadastro/medicamento', MedicamentoCreateView.as_view(), name='cadastro_medicamento'),
    path('entrada/', EntradaMedicamentoCreateView.as_view(), name='entrada_medicamento_create'),
    
    # Lista de Medicamentos
    path('listar/', MedicamentoListView.as_view(), name='listar_medicamentos'),
    path('editar/medicamento/<int:pk>/', MedicamentoUpdateView.as_view(), name='editar_medicamento_info'),
    path('excluir/medicamento/<int:pk>/', MedicamentoDeleteView.as_view(), name='excluir_medicamento_info'),
    
    # Nova view - Controle de Validade (principal)
    path('estoque/', MedicamentoEstoqueListView.as_view(), name='medicamento_estoque'),
    
    # View antiga - Entradas detalhadas (mantida para compatibilidade)
    path('entradas/', EntradaMedicamentoListView.as_view(), name='medicamento_entradas'),
    
    # Notificações
    path('notificacoes/', NotificacoesListView.as_view(), name='medicamento_notificacoes'),
    path('api/notificacoes/', NotificacoesAPIView.as_view(), name='medicamento_notificacoes_api'),
    
    path('editar/<int:pk>/', EntradaMedicamentoUpdateView.as_view(), name='editar_medicamento'),
    path('excluir/<int:pk>/', EntradaMedicamentoDeleteView.as_view(), name='excluir_medicamento'),
]