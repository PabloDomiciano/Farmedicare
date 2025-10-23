from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CadastroUsuarioView, UsuarioListView, UsuarioUpdateView, UsuarioDeleteView

urlpatterns = [
    path('', auth_views.LoginView.as_view(
        template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(),
        name='logout'),
    path("registrar/", CadastroUsuarioView.as_view(), name="registrar"),
    
    # Lista de Usuários
    path('listar/', UsuarioListView.as_view(), name='listar_usuarios'),
    path('editar/<int:pk>/', UsuarioUpdateView.as_view(), name='editar_usuario'),
    path('excluir/<int:pk>/', UsuarioDeleteView.as_view(), name='excluir_usuario'),

]