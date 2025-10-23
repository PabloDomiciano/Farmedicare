from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import ListView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from .forms import UsuarioCadastroForm, UsuarioUpdateForm

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