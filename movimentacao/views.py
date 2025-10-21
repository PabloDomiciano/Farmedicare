from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView, ListView
from django.utils import timezone
from .models import Categoria, Movimentacao, Parcela
from .forms import MovimentacaoForm


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
        return kwargs

    def form_valid(self, form):
        # Define o usuário logado como cadastrado_por
        form.instance.cadastrada_por = self.request.user
        response = super().form_valid(form)
        self.criar_parcelas(form.instance)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Movimentações",
            "titulo": "Cadastro de Movimentações",
            "subtitulo": "Movimentações são usadas para registrar entradas e saídas de dinheiro na fazenda. As parcelas serão geradas automaticamente.",
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
    fields = ["nome", "tipo"]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    extra_context = {
        "title": "Cadastro de Categorias",
        "titulo": "Cadastro de Categorias",
        "subtitulo": "Categorias são usadas para classificar as movimentações financeiras.",
    }


############ Update Movimentacao ############
class MovimentacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = Movimentacao
    fields = [
        "tipo",
        "parceiros",
        "categoria",
        "valor_total",
        "parcelas",
        "imposto_renda",
        "descricao",
        "data",
        "fazenda",
    ]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    extra_context = {
        "title": "Atualização de Movimentações",
        "titulo": "Atualização de Movimentações",
    }


############ Update Parcela ############
class ParcelaUpdateView(LoginRequiredMixin, UpdateView):
    model = Parcela
    fields = ["valor_pago", "status_pagamento", "data_quitacao"]
    template_name = "formularios/formulario_modelo.html"
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def get_success_url(self):
        # Redireciona para a lista correta baseada no tipo de movimentação
        if self.object.movimentacao.tipo == "receita":
            return reverse_lazy("listar_parcelas_receita")
        else:
            return reverse_lazy("listar_parcelas_despesa")

    def form_valid(self, form):
        # Se o status for alterado para "Pago" e data_quitacao estiver vazia, preenche com hoje
        if form.instance.status_pagamento == "Pago" and not form.instance.data_quitacao:
            form.instance.data_quitacao = datetime.now().date()

        # Se o valor pago for igual ao valor da parcela, marca como pago
        if form.instance.valor_pago >= form.instance.valor_parcela:
            form.instance.status_pagamento = "Pago"
            if not form.instance.data_quitacao:
                form.instance.data_quitacao = datetime.now().date()

        return super().form_valid(form)


############ Update Categoria ############
class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    fields = ["nome", "tipo"]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    extra_context = {
        "title": "Atualização de Categorias",
        "titulo": "Atualização de Categorias",
    }


############ Delete Movimentacao ############
class MovimentacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Movimentacao
    template_name = "formularios/formulario_excluir.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

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
        if self.object.movimentacao.tipo == "receita":
            return reverse_lazy("listar_parcelas_receita")
        else:
            return reverse_lazy("listar_parcelas_despesa")

    extra_context = {
        "title": "Exclusão de Parcelas",
        "titulo_excluir": "Exclusão de Parcelas",
    }


############ Delete Categoria ############
class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = "formularios/formulario_excluir.html"
    success_url = reverse_lazy("pagina_index")
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

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
        return Movimentacao.objects.all().order_by("-data")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["despesas"] = Movimentacao.objects.filter(tipo="despesa")
        context["receitas"] = Movimentacao.objects.filter(tipo="receita")
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
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(tipo="receita")
            .order_by("-data")
            .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calcula os totais para receitas
        total_receitas = 0
        for receita in context["object_list"]:
            total_receitas += receita.valor_total

        context["total_receitas"] = total_receitas

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
    login_url = reverse_lazy("login")  # Altere para o nome da sua URL de login

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(tipo="despesa")
            .order_by("-data")
            .select_related("fazenda", "categoria", "parceiros", "cadastrada_por")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calcula os totais para despesas
        total_despesas = 0
        for despesa in context["object_list"]:
            total_despesas += despesa.valor_total

        context["total_despesas"] = total_despesas

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

    def get_queryset(self):
        return Parcela.objects.filter(
            movimentacao__tipo="receita"
        ).order_by("-data_vencimento").select_related(
            'movimentacao', 
            'movimentacao__parceiros', 
            'movimentacao__categoria'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Parcelas a Receber"
        context["titulo"] = "Parcelas a Receber (Receitas)"
        context["registros"] = "Nenhuma parcela de receita encontrada."
        context["btn_cadastrar"] = "Nova Receita"
        context["today"] = timezone.now().date()
        return context


############ List Parcelas de Despesas (A Pagar) ###########
class ParcelasDespesaListView(LoginRequiredMixin, ListView):
    model = Parcela
    template_name = "parcela/lista_parcelas_despesa.html"
    context_object_name = "parcelas"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return Parcela.objects.filter(
            movimentacao__tipo="despesa"
        ).order_by("-data_vencimento").select_related(
            'movimentacao', 
            'movimentacao__parceiros', 
            'movimentacao__categoria'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Parcelas a Pagar"
        context["titulo"] = "Parcelas a Pagar (Despesas)"
        context["registros"] = "Nenhuma parcela de despesa encontrada."
        context["btn_cadastrar"] = "Nova Despesa"
        context["today"] = timezone.now().date()
        return context


############ List Todas as Parcelas (Legado - manter compatibilidade) ###########
class ParcelasListView(LoginRequiredMixin, ListView):
    model = Parcela
    template_name = "parcela/lista_parcelas.html"
    context_object_name = "parcelas"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return Parcela.objects.all().order_by("-data_vencimento").select_related(
            'movimentacao', 
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
