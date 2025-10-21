from django.urls import path
from .views import (
    ParceirosListView, 
    ParceirosCreateView, 
    ParceirosUpdateView, 
    ParceirosDeleteView,
    FazendaListView,
    FazendaCreateView,
    FazendaUpdateView,
    FazendaDeleteView
)

urlpatterns = [
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
]