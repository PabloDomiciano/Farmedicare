from django.urls import path
from .views import (
    ParceirosListView, 
    ParceirosCreateView, 
    ParceirosUpdateView, 
    ParceirosDeleteView,
    FazendaListView,
    FazendaCreateView,
    FazendaUpdateView,
    FazendaDeleteView,
    selecionar_fazenda,
    trocar_fazenda,
    criar_fazenda_inicial,
    cadastrar_funcionario,
    listar_funcionarios,
    remover_funcionario,
    adicionar_funcionario_existente,
)

urlpatterns = [
    # URLs de Sistema Multi-Tenant
    path('selecionar-fazenda/', selecionar_fazenda, name='selecionar_fazenda'),
    path('trocar-fazenda/', trocar_fazenda, name='trocar_fazenda'),
    path('criar-fazenda/', criar_fazenda_inicial, name='criar_fazenda'),
    
    # URLs de Parceiros
    path('parceiros/', ParceirosListView.as_view(), name='listar_parceiros'),
    path('parceiros/cadastrar/', ParceirosCreateView.as_view(), name='cadastrar_parceiro'),
    path('parceiros/editar/<int:pk>/', ParceirosUpdateView.as_view(), name='editar_parceiro'),
    path('parceiros/excluir/<int:pk>/', ParceirosDeleteView.as_view(), name='excluir_parceiro'),
    
    # URLs de Fazendas
    path('fazendas/', FazendaListView.as_view(), name='listar_fazendas'),
    path('fazendas/cadastrar/', FazendaCreateView.as_view(), name='cadastrar_fazenda'),
    path('fazendas/editar/<int:pk>/', FazendaUpdateView.as_view(), name='editar_fazenda'),
    path('fazendas/excluir/<int:pk>/', FazendaDeleteView.as_view(), name='excluir_fazenda'),
    
    # URLs de Funcionários
    path('fazendas/<int:fazenda_id>/funcionarios/', listar_funcionarios, name='listar_funcionarios'),
    path('fazendas/<int:fazenda_id>/funcionarios/cadastrar/', cadastrar_funcionario, name='cadastrar_funcionario'),
    path('fazendas/<int:fazenda_id>/funcionarios/adicionar-existente/', adicionar_funcionario_existente, name='adicionar_funcionario_existente'),
    path('fazendas/<int:fazenda_id>/funcionarios/<int:funcionario_id>/remover/', remover_funcionario, name='remover_funcionario'),
]