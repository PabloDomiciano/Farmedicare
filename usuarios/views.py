from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.shortcuts import redirect
from .forms import UsuarioCadastroForm, UsuarioUpdateForm


class CustomLoginView(LoginView):
    """View customizada de login com mensagens de sucesso/erro"""
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Login bem-sucedido - exibe mensagem de boas-vindas na página index"""
        messages.success(
            self.request,
            f'Bem-vindo(a) ao sistema, {form.get_user().get_full_name() or form.get_user().username}!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Mensagem de erro ao falhar login - exibe na própria página de login"""
        messages.error(
            self.request,
            'Usuário ou senha incorretos. Por favor, tente novamente.'
        )
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """View customizada de logout com mensagem"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Você saiu do sistema. Até logo!')
        return super().dispatch(request, *args, **kwargs)


class CadastroUsuarioView(CreateView):
    model = User
    form_class = UsuarioCadastroForm
    template_name = 'usuarios/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Adiciona ao grupo Funcionario
        grupo, criado = Group.objects.get_or_create(name='Funcionario')
        self.object.groups.add(grupo)
        
        # Define que o usuário está ativo
        self.object.is_active = True
        self.object.save()
        
        messages.success(
            self.request,
            'Conta criada com sucesso! Agora você pode fazer login.'
        )
        
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor, corrija os erros abaixo.'
        )
        return super().form_invalid(form)


############ List Usuários ###########
class UsuarioListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "usuarios/lista_usuarios.html"
    context_object_name = "usuarios"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return User.objects.all().order_by("-date_joined").prefetch_related('groups')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista de Usuários"
        context["titulo"] = "Usuários"
        return context


############ Update Usuário ###########
class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UsuarioUpdateForm
    template_name = "usuarios/formulario_usuario.html"
    success_url = reverse_lazy("listar_usuarios")
    login_url = reverse_lazy("login")

    extra_context = {
        "title": "Edição de Usuário",
        "titulo": "Edição de Usuário",
        "subtitulo": "Edite as informações do usuário abaixo.",
    }


############ Delete Usuário ###########
class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "formularios/formulario_excluir.html"
    success_url = reverse_lazy("listar_usuarios")
    login_url = reverse_lazy("login")

    extra_context = {
        "title": "Exclusão de Usuário",
        "titulo_excluir": "Exclusão de Usuário",
    }
    
    def delete(self, request, *args, **kwargs):
        usuario = self.get_object()
        username = usuario.username
        nome_completo = usuario.get_full_name() or 'Nome não informado'
        
        messages.success(
            self.request,
            f'🗑️ Usuário "{username}" excluído com sucesso! Nome: {nome_completo}'
        )
        return super().delete(request, *args, **kwargs)