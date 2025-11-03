from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView, ListView
from django.utils import timezone
from django.db.models import Q
from .models import Categoria, Movimentacao, Parcela
from .forms import MovimentacaoForm, CategoriaForm, ParcelaForm
from .filters import MovimentacaoFilter, ParcelaFilter


# Create your views here.

############  CRUD das entidades Movimentacao, Parcela, Categoria  ############


############ Create Movimentacao ############
class MovimentacaoCreateView(LoginRequiredMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = "movimentacao/cadastro_movimentacao.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['fazenda'] = self.request.fazenda_ativa
        return kwargs

    def form_valid(self, form):
        # Define o usuário logado como cadastrado_por
        form.instance.cadastrada_por = self.request.user
        # Define a fazenda ativa
        form.instance.fazenda = self.request.fazenda_ativa
        # As parcelas são geradas automaticamente pelo método save() do modelo
        response = super().form_valid(form)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Movimentações",
            "titulo": "Cadastro de Movimentações",
            "subtitulo": "Movimentações são usadas para registrar entradas e saídas de dinheiro na fazenda. As parcelas serão geradas automaticamente.",
        })
        return context


############ Create Receita (Movimentação com tipo fixo) ############
class ReceitaCreateView(LoginRequiredMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = "movimentacao/cadastro_movimentacao.html"
    success_url = reverse_lazy("listar_movimentacao_receita")
    login_url = reverse_lazy("login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['fazenda'] = self.request.fazenda_ativa
        kwargs['tipo_fixo'] = 'receita'  # Define tipo fixo como receita
        return kwargs

    def form_valid(self, form):
        form.instance.cadastrada_por = self.request.user
        form.instance.fazenda = self.request.fazenda_ativa
        # Não precisa mais definir tipo - será obtido da categoria
        messages.success(
            self.request,
            f'✅ Receita cadastrada com sucesso! Valor: R$ {form.instance.valor_total:.2f}'
        )
        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao cadastrar receita. Por favor, verifique os campos e tente novamente.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Receita",
            "titulo": "Nova Receita",
            "subtitulo": "Registre uma nova entrada de dinheiro. O formulário está configurado para receitas e as categorias mostradas são apenas de receitas.",
        })
        return context


############ Create Despesa (Movimentação com tipo fixo) ############
class DespesaCreateView(LoginRequiredMixin, CreateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = "movimentacao/cadastro_movimentacao.html"
    success_url = reverse_lazy("listar_movimentacao_despesa")
    login_url = reverse_lazy("login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['fazenda'] = self.request.fazenda_ativa
        kwargs['tipo_fixo'] = 'despesa'  # Define tipo fixo como despesa
        return kwargs

    def form_valid(self, form):
        form.instance.cadastrada_por = self.request.user
        form.instance.fazenda = self.request.fazenda_ativa
        # Não precisa mais definir tipo - será obtido da categoria
        messages.success(
            self.request,
            f'✅ Despesa cadastrada com sucesso! Valor: R$ {form.instance.valor_total:.2f}'
        )
        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao cadastrar despesa. Por favor, verifique os campos e tente novamente.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Despesa",
            "titulo": "Nova Despesa",
            "subtitulo": "Registre uma nova saída de dinheiro. O formulário está configurado para despesas e as categorias mostradas são apenas de despesas.",
        })
        return context


############ Create Parcela ############
class ParcelaCreateView(LoginRequiredMixin, CreateView):
    model = Parcela
    fields = [
        "movimentacao",
        "ordem_parcela",
        "valor_parcela",
        "data_vencimento",
        "valor_pago",
        "status_pagamento",
        "data_quitacao",
    ]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    extra_context = {
        "title": "Cadastro de Parcelas",
        "titulo": "Cadastro de Parcelas",
        "subtitulo": "Parcelas são usadas para dividir o valor de uma movimentação em várias partes.",
    }


############ Create Categoria ############
class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria/formulario_categoria.html"
    success_url = reverse_lazy("listar_categorias")
    login_url = reverse_lazy("login")

    def form_valid(self, form):
        """Associa a categoria à fazenda ativa"""
        form.instance.fazenda = self.request.fazenda_ativa
        messages.success(
            self.request,
            f'✅ Categoria "{form.instance.nome}" cadastrada com sucesso!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao cadastrar categoria. Verifique os dados.'
        )
        return super().form_invalid(form)

    extra_context = {
        "title": "Cadastro de Categoria",
        "titulo": "Cadastro de Categoria",
        "subtitulo": "Categorias são usadas para classificar as movimentações financeiras.",
    }


############ Update Movimentacao ############
class MovimentacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Movimentacao
    form_class = MovimentacaoForm
    template_name = "movimentacao/cadastro_movimentacao.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['fazenda'] = self.request.fazenda_ativa
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Movimentação atualizada com sucesso!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao atualizar movimentação. Verifique os dados e tente novamente.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Edição de Movimentação",
            "titulo": "Edição de Movimentação",
            "subtitulo": "Edite as informações da movimentação abaixo.",
        })
        return context


############ Update Parcela ############
class ParcelaUpdateView(LoginRequiredMixin, UpdateView):
    model = Parcela
    form_class = ParcelaForm
    template_name = "parcela/formulario_parcela.html"
    login_url = reverse_lazy("login")

    def get_success_url(self):
        # Redireciona para a lista correta baseada no tipo de movimentação
        if self.object.movimentacao.categoria.tipo == "receita":
            return reverse_lazy("listar_parcelas_receita")
        else:
            return reverse_lazy("listar_parcelas_despesa")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parcela = self.object
        movimentacao = parcela.movimentacao
        
        context.update({
            'title': f'Editar Parcela {parcela.ordem_parcela}/{movimentacao.parcelas}',
            'titulo': f'Editar Parcela {parcela.ordem_parcela} de {movimentacao.parcelas}',
            'subtitulo': f'{movimentacao.categoria.get_tipo_display()}: {movimentacao.categoria}' + (f' - {movimentacao.parceiros}' if movimentacao.parceiros else ''),
            'movimentacao': movimentacao,
            'total_parcelas': movimentacao.parcelas,
            'tipo_movimentacao': movimentacao.categoria.tipo,
        })
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Parcela {form.instance.ordem_parcela} atualizada com sucesso!'
        )
        return super().form_valid(form)


############ Update Categoria ############
class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "categoria/formulario_categoria.html"
    success_url = reverse_lazy("listar_categorias")
    login_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Categoria "{form.instance.nome}" atualizada com sucesso!'
        )
        return super().form_valid(form)

    extra_context = {
        "title": "Edição de Categoria",
        "titulo": "Edição de Categoria",
        "subtitulo": "Edite as informações da categoria abaixo.",
    }


############ Delete Movimentacao ############
class MovimentacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Movimentacao
    template_name = "formularios/formulario_excluir.html"
    login_url = reverse_lazy("login")

    def get_success_url(self):
        # Redireciona para a lista correta baseada no tipo de movimentação
        if self.object.categoria.tipo == "receita":
            return reverse_lazy("listar_movimentacao_receita")
        else:
            return reverse_lazy("listar_movimentacao_despesa")

    def delete(self, request, *args, **kwargs):
        movimentacao = self.get_object()
        tipo = movimentacao.categoria.get_tipo_display()
        parceiro = movimentacao.parceiros.nome if movimentacao.parceiros else "Sem parceiro"
        valor = movimentacao.valor_total
        
        messages.success(
            self.request,
            f'🗑️ {tipo} excluída com sucesso! Parceiro: {parceiro} - Valor: R$ {valor:.2f}'
        )
        return super().delete(request, *args, **kwargs)

    extra_context = {
        "title": "Exclusão de Movimentações",
        "titulo_excluir": "Exclusão de Movimentações",
    }


############ Delete Parcela ############
class ParcelaDeleteView(LoginRequiredMixin, DeleteView):
    model = Parcela
    template_name = "formularios/formulario_excluir.html"
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def get_success_url(self):
        # Redireciona para a lista correta baseada no tipo de movimentação
        if self.object.movimentacao.categoria.tipo == "receita":
            return reverse_lazy("listar_parcelas_receita")
        else:
            return reverse_lazy("listar_parcelas_despesa")

    def delete(self, request, *args, **kwargs):
        parcela = self.get_object()
        tipo = parcela.movimentacao.categoria.get_tipo_display()
        ordem = parcela.ordem_parcela
        total_parcelas = parcela.movimentacao.parcelas
        parceiro = parcela.movimentacao.parceiros.nome if parcela.movimentacao.parceiros else "Sem parceiro"
        valor = parcela.valor_parcela
        
        messages.success(
            self.request,
            f'🗑️ Parcela {ordem}/{total_parcelas} excluída com sucesso! {tipo}: {parceiro} - Valor: R$ {valor:.2f}'
        )
        return super().delete(request, *args, **kwargs)

    extra_context = {
        "title": "Exclusão de Parcelas",
        "titulo_excluir": "Exclusão de Parcelas",
    }


############ Delete Categoria ############
class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = "formularios/formulario_excluir.html"
    success_url = reverse_lazy("listar_categorias")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        categoria_nome = categoria.nome
        categoria_tipo = categoria.get_tipo_display()
        
        messages.success(
            self.request,
            f'🗑️ Categoria "{categoria_nome}" ({categoria_tipo}) excluída com sucesso!'
        )
        return super().delete(request, *args, **kwargs)

    extra_context = {
        "title": "Exclusão de Categorias",
        "titulo_excluir": "Exclusão de Categorias",
    }


############ List Movimentação Genérica ############
class MovimentacaoListView(LoginRequiredMixin, ListView):
    model = Movimentacao
    template_name = "movimentacao/lista_movimentacoes.html"
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def get_queryset(self):
        """Filtra movimentações apenas da fazenda ativa"""
        if hasattr(self.request, 'fazenda_ativa'):
            return (
                Movimentacao.objects.filter(fazenda=self.request.fazenda_ativa)
                .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
                .order_by("-data")
            )
        return Movimentacao.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request, 'fazenda_ativa'):
            context["despesas"] = (
                Movimentacao.objects.filter(
                    categoria__tipo="despesa",
                    fazenda=self.request.fazenda_ativa
                )
                .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
            )
            context["receitas"] = (
                Movimentacao.objects.filter(
                    categoria__tipo="receita",
                    fazenda=self.request.fazenda_ativa
                )
                .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
            )
        return context

    extra_context = {
        "title": "Lista de Movimentações",
        "titulo": "Movimentações",
        "subtitulo": "Aqui você pode visualizar todas as movimentações financeiras registradas.",
        "registros": "Nenhum registro encontrado.",
    }


############ List Movimentação Receita ############
class MovimentacaoReceitaListView(LoginRequiredMixin, ListView):
    model = Movimentacao
    template_name = "receita/lista_receita.html"
    login_url = reverse_lazy("login")
    paginate_by = 20
    filterset_class = MovimentacaoFilter

    def get_queryset(self):
        """Filtra receitas apenas da fazenda ativa"""
        queryset = (
            super()
            .get_queryset()
            .filter(
                categoria__tipo="receita",
                fazenda=self.request.fazenda_ativa
            )
            .order_by("-data")
            .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
        )
        
        # Pesquisa por texto (busca em todos os registros)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(descricao__icontains=search_query) |
                Q(parceiros__nome__icontains=search_query) |
                Q(categoria__nome__icontains=search_query) |
                Q(fazenda__nome__icontains=search_query)
            )
        
        # Aplicar filtros
        self.filterset = MovimentacaoFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Adicionar parâmetro de pesquisa ao contexto
        context['search_query'] = self.request.GET.get('search', '')

        # Calcula os totais para receitas (apenas itens filtrados)
        total_receitas = sum(receita.valor_total for receita in self.filterset.qs)
        
        context["total_receitas"] = total_receitas
        context["filter"] = self.filterset

        return context

    extra_context = {
        "title": "Lista de Receitas",
        "titulo": "Receitas",
        "subtitulo": "Aqui você pode visualizar todas as receitas registradas.",
        "registros": "Nenhuma receita encontrada.",
        "btn_cadastrar": "Nova Receita",
    }


############ List Movimentação Despesa ############
class MovimentacaoDespesaListView(LoginRequiredMixin, ListView):
    model = Movimentacao
    template_name = "despesa/lista_despesa.html"
    login_url = reverse_lazy("login")
    paginate_by = 20
    filterset_class = MovimentacaoFilter

    def get_queryset(self):
        """Filtra despesas apenas da fazenda ativa"""
        queryset = (
            super()
            .get_queryset()
            .filter(
                categoria__tipo="despesa",
                fazenda=self.request.fazenda_ativa
            )
            .order_by("-data")
            .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
        )
        
        # Pesquisa por texto (busca em todos os registros)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(descricao__icontains=search_query) |
                Q(parceiros__nome__icontains=search_query) |
                Q(categoria__nome__icontains=search_query) |
                Q(fazenda__nome__icontains=search_query)
            )
        
        # Aplicar filtros
        self.filterset = MovimentacaoFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Adicionar parâmetro de pesquisa ao contexto
        context['search_query'] = self.request.GET.get('search', '')

        # Calcula os totais para despesas (apenas itens filtrados)
        total_despesas = sum(despesa.valor_total for despesa in self.filterset.qs)
        
        context["total_despesas"] = total_despesas
        context["filter"] = self.filterset

        return context

    extra_context = {
        "title": "Lista de Despesas",
        "titulo": "Despesas",
        "subtitulo": "Aqui você pode visualizar todas as despesas registradas.",
        "registros": "Nenhuma despesa encontrada.",
        "btn_cadastrar": "Nova Despesa",
    }


############ List Parcelas de Receitas (A Receber) ###########
class ParcelasReceitaListView(LoginRequiredMixin, ListView):
    model = Parcela
    template_name = "parcela/lista_parcelas_receita.html"
    context_object_name = "parcelas"
    login_url = reverse_lazy("login")
    paginate_by = 20
    filterset_class = ParcelaFilter

    def get_queryset(self):
        fazenda_ativa = self.request.fazenda_ativa if hasattr(self.request, 'fazenda_ativa') else None
        if not fazenda_ativa:
            return Parcela.objects.none()
        
        queryset = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            movimentacao__categoria__tipo="receita"
        ).order_by("-data_vencimento").select_related(
            'movimentacao', 
            'movimentacao__fazenda',
            'movimentacao__parceiros', 
            'movimentacao__categoria'
        )
        
        # Pesquisa por texto (busca em todos os registros)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(movimentacao__descricao__icontains=search_query) |
                Q(movimentacao__parceiros__nome__icontains=search_query) |
                Q(movimentacao__categoria__nome__icontains=search_query) |
                Q(status_pagamento__icontains=search_query)
            )
        
        # Aplicar filtros
        self.filterset = ParcelaFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adicionar parâmetro de pesquisa ao contexto
        context['search_query'] = self.request.GET.get('search', '')
        
        context["title"] = "Parcelas a Receber"
        context["titulo"] = "Parcelas a Receber (Receitas)"
        context["registros"] = "Nenhuma parcela de receita encontrada."
        context["btn_cadastrar"] = "Nova Receita"
        context["today"] = timezone.now().date()
        context["filter"] = self.filterset
        return context


############ List Parcelas de Despesas (A Pagar) ###########
class ParcelasDespesaListView(LoginRequiredMixin, ListView):
    model = Parcela
    template_name = "parcela/lista_parcelas_despesa.html"
    context_object_name = "parcelas"
    login_url = reverse_lazy("login")
    paginate_by = 20
    filterset_class = ParcelaFilter

    def get_queryset(self):
        fazenda_ativa = self.request.fazenda_ativa if hasattr(self.request, 'fazenda_ativa') else None
        if not fazenda_ativa:
            return Parcela.objects.none()
        
        queryset = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            movimentacao__categoria__tipo="despesa"
        ).order_by("-data_vencimento").select_related(
            'movimentacao', 
            'movimentacao__fazenda',
            'movimentacao__parceiros', 
            'movimentacao__categoria'
        )
        
        # Pesquisa por texto (busca em todos os registros)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(movimentacao__descricao__icontains=search_query) |
                Q(movimentacao__parceiros__nome__icontains=search_query) |
                Q(movimentacao__categoria__nome__icontains=search_query) |
                Q(status_pagamento__icontains=search_query)
            )
        
        # Aplicar filtros
        self.filterset = ParcelaFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adicionar parâmetro de pesquisa ao contexto
        context['search_query'] = self.request.GET.get('search', '')
        
        context["title"] = "Parcelas a Pagar"
        context["titulo"] = "Parcelas a Pagar (Despesas)"
        context["registros"] = "Nenhuma parcela de despesa encontrada."
        context["btn_cadastrar"] = "Nova Despesa"
        context["today"] = timezone.now().date()
        context["filter"] = self.filterset
        return context


############ List Todas as Parcelas (Legado - manter compatibilidade) ###########
class ParcelasListView(LoginRequiredMixin, ListView):
    model = Parcela
    template_name = "parcela/lista_parcelas.html"
    context_object_name = "parcelas"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        fazenda_ativa = self.request.fazenda_ativa if hasattr(self.request, 'fazenda_ativa') else None
        if not fazenda_ativa:
            return Parcela.objects.none()
        
        return Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa
        ).order_by("-data_vencimento").select_related(
            'movimentacao', 
            'movimentacao__fazenda',
            'movimentacao__parceiros', 
            'movimentacao__categoria'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Todas as Parcelas"
        context["titulo"] = "Todas as Parcelas"
        context["registros"] = "Nenhuma parcela encontrada."
        context["btn_cadastrar"] = "Nova Movimentação"
        context["today"] = timezone.now().date()
        return context


############ List Categorias ###########
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "categoria/lista_categorias.html"
    context_object_name = "categorias"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        """Filtra categorias apenas da fazenda ativa"""
        if hasattr(self.request, 'fazenda_ativa'):
            return Categoria.objects.filter(
                fazenda=self.request.fazenda_ativa
            ).order_by("tipo", "nome")
        return Categoria.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista de Categorias"
        context["titulo"] = "Categorias"
        
        # Usar apenas uma query com filtro em Python (já carregado)
        all_categorias = list(self.get_queryset())
        context["categorias_receita"] = [c for c in all_categorias if c.tipo == "receita"]
        context["categorias_despesa"] = [c for c in all_categorias if c.tipo == "despesa"]
        
        return context
