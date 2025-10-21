from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Fazenda, Parceiros
from .forms import ParceirosForm, FazendaForm

# ============================================
# VIEWS PARA PARCEIROS
# ============================================

class ParceirosListView(LoginRequiredMixin, ListView):
    model = Parceiros
    template_name = 'parceiros/lista_parceiros.html'
    context_object_name = 'parceiros'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Parceiros'
        return context

class ParceirosCreateView(LoginRequiredMixin, CreateView):
    model = Parceiros
    form_class = ParceirosForm
    template_name = 'parceiros/cadastro_parceiro.html'
    success_url = reverse_lazy('listar_parceiros')
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Parceiro'
        context['subtitulo'] = 'Atualize as informações do parceiro'
        return context

class ParceirosDeleteView(LoginRequiredMixin, DeleteView):
    model = Parceiros
    template_name = 'formularios/formulario_excluir.html'
    success_url = reverse_lazy('listar_parceiros')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Excluir Parceiro'
        context['objeto'] = self.object
        context['tipo'] = 'parceiro'
        return context

# ============================================
# VIEWS PARA FAZENDAS
# ============================================

class FazendaListView(LoginRequiredMixin, ListView):
    model = Fazenda
    template_name = 'fazendas/lista_fazendas.html'
    context_object_name = 'fazendas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Fazendas'
        return context

class FazendaCreateView(LoginRequiredMixin, CreateView):
    model = Fazenda
    form_class = FazendaForm
    template_name = 'fazendas/cadastro_fazenda.html'
    success_url = reverse_lazy('listar_fazendas')
    
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Fazenda'
        context['subtitulo'] = 'Atualize as informações da fazenda'
        return context

class FazendaDeleteView(LoginRequiredMixin, DeleteView):
    model = Fazenda
    template_name = 'formularios/formulario_excluir.html'
    success_url = reverse_lazy('listar_fazendas')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Excluir Fazenda'
        context['objeto'] = self.object
        context['tipo'] = 'fazenda'
        return context 



