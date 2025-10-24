from django.contrib import admin
from .models import Medicamento, EntradaMedicamento, SaidaMedicamento


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'fazenda', 'quantidade_total', 'proxima_validade']
    list_filter = ['fazenda']
    search_fields = ['nome']


@admin.register(EntradaMedicamento)
class EntradaMedicamentoAdmin(admin.ModelAdmin):
    list_display = ['medicamento', 'quantidade', 'validade', 'valor_medicamento', 'data_cadastro', 'cadastrada_por']
    list_filter = ['medicamento', 'validade', 'data_cadastro']
    search_fields = ['medicamento__nome', 'observacao']
    date_hierarchy = 'data_cadastro'


@admin.register(SaidaMedicamento)
class SaidaMedicamentoAdmin(admin.ModelAdmin):
    list_display = ['medicamento', 'quantidade', 'data_saida', 'registrada_por', 'motivo']
    list_filter = ['medicamento', 'data_saida']
    search_fields = ['medicamento__nome', 'motivo']
    date_hierarchy = 'data_saida'
    readonly_fields = ['data_saida']    