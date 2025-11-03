from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User

from .models import Fazenda, Parceiros, PerfilUsuario
from .forms import ParceirosForm, FazendaForm, FuncionarioForm, AdicionarFuncionarioExistenteForm


# ============================================
# VIEWS PARA SISTEMA MULTI-TENANT
# ============================================

@login_required
def selecionar_fazenda(request):
    """
    View para o usuário selecionar qual fazenda deseja acessar
    """
    perfil = request.user.perfil
    
    # Busca fazendas do usuário
    fazendas = perfil.fazendas.filter(ativa=True) | Fazenda.objects.filter(dono=request.user, ativa=True)
    fazendas = fazendas.distinct()
    
    if request.method == 'POST':
        fazenda_id = request.POST.get('fazenda_id')
        fazenda = get_object_or_404(Fazenda, id=fazenda_id)
        
        # Verifica se o usuário tem acesso
        if fazenda in fazendas:
            request.session['fazenda_ativa_id'] = fazenda.id
            messages.success(request, f'✅ Fazenda "{fazenda.nome}" selecionada com sucesso!')
            return redirect('pagina_index')
        else:
            messages.error(request, '❌ Você não tem permissão para acessar esta fazenda.')
    
    context = {
        'fazendas': fazendas,
        'titulo': 'Selecionar Fazenda',
    }
    return render(request, 'fazendas/selecionar_fazenda.html', context)


@login_required
def trocar_fazenda(request):
    """
    View rápida para trocar de fazenda
    """
    return selecionar_fazenda(request)


@login_required
def criar_fazenda_inicial(request):
    """
    View para criar a primeira fazenda do produtor
    """
    # Verifica se o usuário já tem alguma fazenda
    perfil = request.user.perfil
    fazendas = perfil.fazendas.filter(ativa=True) | Fazenda.objects.filter(dono=request.user, ativa=True)
    
    if fazendas.exists():
        return redirect('selecionar_fazenda')
    
    if request.method == 'POST':
        form = FazendaForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                fazenda = form.save(commit=False)
                fazenda.dono = request.user
                fazenda.save()
                
                # Adiciona o usuário à fazenda
                perfil.fazendas.add(fazenda)
                
                # Define como produtor se ainda não for
                if perfil.tipo != 'produtor':
                    perfil.tipo = 'produtor'
                    perfil.save()
                
                # Define como fazenda ativa
                request.session['fazenda_ativa_id'] = fazenda.id
                
                messages.success(request, f'🎉 Fazenda "{fazenda.nome}" criada com sucesso! Bem-vindo ao FarMedicare!')
                return redirect('pagina_index')
    else:
        form = FazendaForm()
    
    context = {
        'form': form,
        'titulo': 'Criar Primeira Fazenda',
        'subtitulo': 'Vamos começar criando sua fazenda',
    }
    return render(request, 'fazendas/criar_fazenda_inicial.html', context)


# ============================================
# VIEWS PARA PARCEIROS
# ============================================

class ParceirosListView(LoginRequiredMixin, ListView):
    model = Parceiros
    template_name = 'parceiros/lista_parceiros.html'
    context_object_name = 'parceiros'
    
    def get_queryset(self):
        """Filtra apenas parceiros da fazenda ativa"""
        if hasattr(self.request, 'fazenda_ativa'):
            return Parceiros.objects.filter(fazenda=self.request.fazenda_ativa)
        return Parceiros.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Parceiros'
        return context


class ParceirosCreateView(LoginRequiredMixin, CreateView):
    model = Parceiros
    form_class = ParceirosForm
    template_name = 'parceiros/cadastro_parceiro.html'
    success_url = reverse_lazy('listar_parceiros')
    
    def form_valid(self, form):
        """Associa o parceiro à fazenda ativa"""
        form.instance.fazenda = self.request.fazenda_ativa
        messages.success(self.request, f'✅ Parceiro "{form.instance.nome}" cadastrado com sucesso!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Novo Parceiro'
        context['subtitulo'] = 'Cadastre um novo parceiro comercial'
        return context


class ParceirosUpdateView(LoginRequiredMixin, UpdateView):
    model = Parceiros
    form_class = ParceirosForm
    template_name = 'parceiros/cadastro_parceiro.html'
    success_url = reverse_lazy('listar_parceiros')
    
    def get_queryset(self):
        """Permite editar apenas parceiros da fazenda ativa"""
        if hasattr(self.request, 'fazenda_ativa'):
            return Parceiros.objects.filter(fazenda=self.request.fazenda_ativa)
        return Parceiros.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Parceiro'
        context['subtitulo'] = 'Atualize as informações do parceiro'
        return context


class ParceirosDeleteView(LoginRequiredMixin, DeleteView):
    model = Parceiros
    template_name = 'formularios/formulario_excluir.html'
    success_url = reverse_lazy('listar_parceiros')
    
    def get_queryset(self):
        """Permite excluir apenas parceiros da fazenda ativa"""
        if hasattr(self.request, 'fazenda_ativa'):
            return Parceiros.objects.filter(fazenda=self.request.fazenda_ativa)
        return Parceiros.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Excluir Parceiro'
        context['objeto'] = self.object
        context['tipo'] = 'parceiro'
        return context
    
    def delete(self, request, *args, **kwargs):
        parceiro = self.get_object()
        parceiro_nome = parceiro.nome
        telefone = parceiro.telefone or 'Não informado'
        
        messages.success(
            self.request,
            f'🗑️ Parceiro "{parceiro_nome}" excluído com sucesso! Telefone: {telefone}'
        )
        return super().delete(request, *args, **kwargs)


# ============================================
# VIEWS PARA FAZENDAS
# ============================================

class FazendaListView(LoginRequiredMixin, ListView):
    model = Fazenda
    template_name = 'fazendas/lista_fazendas.html'
    context_object_name = 'fazendas'
    
    def get_queryset(self):
        """Lista apenas fazendas que o usuário tem acesso"""
        perfil = self.request.user.perfil
        fazendas = perfil.fazendas.filter(ativa=True) | Fazenda.objects.filter(dono=self.request.user, ativa=True)
        return fazendas.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Fazendas'
        return context


class FazendaCreateView(LoginRequiredMixin, CreateView):
    model = Fazenda
    form_class = FazendaForm
    template_name = 'fazendas/cadastro_fazenda.html'
    success_url = reverse_lazy('listar_fazendas')
    
    def form_valid(self, form):
        """Define o usuário como dono e adiciona à lista de fazendas"""
        with transaction.atomic():
            form.instance.dono = self.request.user
            response = super().form_valid(form)
            
            # Adiciona o usuário à fazenda
            perfil = self.request.user.perfil
            perfil.fazendas.add(self.object)
            
            # Define como produtor se ainda não for
            if perfil.tipo != 'produtor':
                perfil.tipo = 'produtor'
                perfil.save()
            
            messages.success(self.request, f'✅ Fazenda "{self.object.nome}" criada com sucesso!')
            return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Nova Fazenda'
        context['subtitulo'] = 'Cadastre uma nova fazenda ou propriedade rural'
        return context


class FazendaUpdateView(LoginRequiredMixin, UpdateView):
    model = Fazenda
    form_class = FazendaForm
    template_name = 'fazendas/cadastro_fazenda.html'
    success_url = reverse_lazy('listar_fazendas')
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o usuário é o dono da fazenda antes de permitir edição"""
        fazenda = self.get_object()
        if fazenda.dono != request.user:
            messages.error(request, '❌ Apenas o proprietário pode editar esta fazenda.')
            return render(request, 'fazendas/sem_permissao.html')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Permite editar apenas fazendas que o usuário é dono"""
        return Fazenda.objects.filter(dono=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Fazenda'
        context['subtitulo'] = 'Atualize as informações da fazenda'
        return context


class FazendaDeleteView(LoginRequiredMixin, DeleteView):
    model = Fazenda
    template_name = 'formularios/formulario_excluir.html'
    success_url = reverse_lazy('listar_fazendas')
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica se o usuário é o dono da fazenda antes de permitir exclusão"""
        fazenda = self.get_object()
        if fazenda.dono != request.user:
            messages.error(request, '❌ Apenas o proprietário pode excluir esta fazenda.')
            return render(request, 'fazendas/sem_permissao.html')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Permite excluir apenas fazendas que o usuário é dono"""
        return Fazenda.objects.filter(dono=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Excluir Fazenda'
        context['objeto'] = self.object
        context['tipo'] = 'fazenda'
        return context
    
    def delete(self, request, *args, **kwargs):
        fazenda = self.get_object()
        fazenda_nome = fazenda.nome
        cidade = fazenda.cidade or 'Não informada'
        
        messages.success(
            self.request,
            f'🗑️ Fazenda "{fazenda_nome}" excluída com sucesso! Cidade: {cidade}'
        )
        return super().delete(request, *args, **kwargs)


# ============================================
# VIEWS PARA FUNCIONÁRIOS
# ============================================

@login_required
def cadastrar_funcionario(request, fazenda_id):
    """
    View para cadastrar um novo funcionário vinculado a uma fazenda específica.
    Apenas o dono da fazenda pode cadastrar funcionários.
    """
    fazenda = get_object_or_404(Fazenda, id=fazenda_id, dono=request.user)
    
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Cria o usuário e vincula à fazenda
                    user = form.save(fazenda)
                    
                    messages.success(
                        request,
                        f'✅ Funcionário "{user.get_full_name()}" cadastrado com sucesso na fazenda "{fazenda.nome}"!'
                    )
                    return redirect('listar_funcionarios', fazenda_id=fazenda.id)
            except Exception as e:
                messages.error(request, f'❌ Erro ao cadastrar funcionário: {str(e)}')
    else:
        form = FuncionarioForm()
    
    context = {
        'form': form,
        'fazenda': fazenda,
        'titulo': 'Cadastrar Funcionário',
        'subtitulo': f'Adicionar novo funcionário à fazenda {fazenda.nome}',
    }
    return render(request, 'funcionarios/cadastro_funcionario.html', context)


@login_required
def adicionar_funcionario_existente(request, fazenda_id):
    """
    View para adicionar um funcionário já existente a uma fazenda.
    Apenas o dono da fazenda pode adicionar.
    """
    fazenda = get_object_or_404(Fazenda, id=fazenda_id, dono=request.user)
    
    if request.method == 'POST':
        form = AdicionarFuncionarioExistenteForm(request.POST, fazenda=fazenda)
        if form.is_valid():
            funcionario = form.cleaned_data['funcionario']
            
            # Adiciona o funcionário à fazenda
            funcionario.fazendas.add(fazenda)
            
            messages.success(
                request,
                f'✅ Funcionário "{funcionario.user.get_full_name()}" adicionado à fazenda "{fazenda.nome}"!'
            )
            return redirect('listar_funcionarios', fazenda_id=fazenda.id)
    else:
        form = AdicionarFuncionarioExistenteForm(fazenda=fazenda)
    
    # Verifica se há funcionários disponíveis para adicionar
    if not form.fields['funcionario'].queryset.exists():
        messages.warning(
            request,
            'Não há funcionários disponíveis para adicionar. Todos os seus funcionários já estão nesta fazenda.'
        )
        return redirect('listar_funcionarios', fazenda_id=fazenda.id)
    
    context = {
        'form': form,
        'fazenda': fazenda,
        'titulo': 'Adicionar Funcionário Existente',
        'subtitulo': f'Adicionar funcionário à fazenda {fazenda.nome}',
    }
    return render(request, 'funcionarios/adicionar_existente.html', context)


@login_required
def listar_funcionarios(request, fazenda_id):
    """
    View para listar funcionários de uma fazenda específica.
    O dono pode visualizar e gerenciar, funcionários podem apenas visualizar.
    """
    # Verifica se o usuário tem acesso a esta fazenda
    fazenda = get_object_or_404(Fazenda, id=fazenda_id)
    perfil = request.user.perfil
    
    # Verifica se o usuário é dono ou funcionário desta fazenda
    if fazenda.dono != request.user and fazenda not in perfil.fazendas.all():
        messages.error(request, '❌ Você não tem permissão para acessar esta fazenda.')
        return redirect('selecionar_fazenda')
    
    # Busca funcionários vinculados a esta fazenda
    funcionarios = PerfilUsuario.objects.filter(
        fazendas=fazenda,
        tipo='funcionario'
    ).select_related('user')
    
    # Verifica se existem funcionários de outras fazendas do mesmo dono
    # que podem ser adicionados a esta fazenda (apenas para donos)
    funcionarios_disponiveis = 0
    if fazenda.dono == request.user:
        funcionarios_disponiveis = PerfilUsuario.objects.filter(
            tipo='funcionario',
            fazendas__dono=request.user
        ).exclude(
            fazendas=fazenda
        ).distinct().count()
    
    context = {
        'fazenda': fazenda,
        'funcionarios': funcionarios,
        'funcionarios_disponiveis': funcionarios_disponiveis,
        'titulo': 'Funcionários',
        'subtitulo': f'Funcionários da fazenda {fazenda.nome}',
    }
    return render(request, 'funcionarios/lista_funcionarios.html', context)


@login_required
def remover_funcionario(request, fazenda_id, funcionario_id):
    """
    View para remover um funcionário de uma fazenda específica.
    Apenas o dono da fazenda pode remover funcionários.
    """
    fazenda = get_object_or_404(Fazenda, id=fazenda_id, dono=request.user)
    perfil = get_object_or_404(PerfilUsuario, id=funcionario_id, tipo='funcionario')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Remove o vínculo com a fazenda
            perfil.fazendas.remove(fazenda)
            
            # Se não tem mais fazendas vinculadas, pode desativar o usuário
            if perfil.fazendas.count() == 0:
                perfil.user.is_active = False
                perfil.user.save()
            
            messages.success(
                request,
                f'✅ Funcionário "{perfil.user.get_full_name()}" removido da fazenda "{fazenda.nome}"!'
            )
            return redirect('listar_funcionarios', fazenda_id=fazenda.id)
    
    context = {
        'fazenda': fazenda,
        'funcionario': perfil,
        'titulo': 'Remover Funcionário',
    }
    return render(request, 'funcionarios/remover_funcionario.html', context)
