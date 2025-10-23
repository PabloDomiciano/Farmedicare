from django.urls import path

# Importação das views de Criação
from medicamento import views
from movimentacao.views import MovimentacaoCreateView, ParcelaCreateView,CategoriaCreateView
# Importação das views de Edição
from movimentacao.views import MovimentacaoUpdateView, ParcelaUpdateView, CategoriaUpdateView
# Importação das views de Exclusão
from movimentacao.views import MovimentacaoDeleteView, ParcelaDeleteView, CategoriaDeleteView

# Importação das views de Listagem
from movimentacao.views import (
    MovimentacaoReceitaListView, 
    MovimentacaoDespesaListView, 
    ParcelasListView,
    ParcelasReceitaListView,
    ParcelasDespesaListView,
    CategoriaListView
)

urlpatterns = [
    path('cadastrar/movimentacao/', MovimentacaoCreateView.as_view(), name='cadastrar_movimentacao'),
    path('cadastrar/parcela/', ParcelaCreateView.as_view(), name='cadastrar_parcela'),
    path('cadastrar/categoria/', CategoriaCreateView.as_view(), name='cadastrar_categoria'),

    path('editar/movimentacao/<int:pk>/', MovimentacaoUpdateView.as_view(), name='editar_movimentacao'),
    path('editar/parcela/<int:pk>/', ParcelaUpdateView.as_view(), name='editar_parcela'),
    path('editar/categoria/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),

    path('excluir/movimentacao/<int:pk>/', MovimentacaoDeleteView.as_view(), name='excluir_movimentacao'),
    path('excluir/parcela/<int:pk>/', ParcelaDeleteView.as_view(), name='excluir_parcela'),
    path('excluir/categoria/<int:pk>/', CategoriaDeleteView.as_view(), name='excluir_categoria'),

    path('listar/movimentacao/receita/', MovimentacaoReceitaListView.as_view(), name='listar_movimentacao_receita'),
    path('listar/movimentacao/despesa/', MovimentacaoDespesaListView.as_view(), name='listar_movimentacao_despesa'),
    
    # Novas URLs - Parcelas separadas por tipo
    path('listar/parcelas/receita/', ParcelasReceitaListView.as_view(), name='listar_parcelas_receita'),
    path('listar/parcelas/despesa/', ParcelasDespesaListView.as_view(), name='listar_parcelas_despesa'),
    
    # URL antiga mantida para compatibilidade
    path('listar/todas-parcelas/', ParcelasListView.as_view(), name='listar_parcelas'),
    
    # Lista de Categorias
    path('listar/categorias/', CategoriaListView.as_view(), name='listar_categorias'),

]