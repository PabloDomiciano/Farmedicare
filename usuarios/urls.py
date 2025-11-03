from django.urls import path
from .views import (
    CustomLoginView, 
    CustomLogoutView,
    CadastroUsuarioView, 
    UsuarioListView, 
    UsuarioUpdateView, 
    UsuarioDeleteView
)

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path("registrar/", CadastroUsuarioView.as_view(), name="registrar"),
    
    # Lista de Usuários
    path('listar/', UsuarioListView.as_view(), name='listar_usuarios'),
    path('editar/<int:pk>/', UsuarioUpdateView.as_view(), name='editar_usuario'),
    path('excluir/<int:pk>/', UsuarioDeleteView.as_view(), name='excluir_usuario'),

]