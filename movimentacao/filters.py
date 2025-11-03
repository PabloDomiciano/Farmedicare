import django_filters
from django import forms
from .models import Movimentacao, Parcela


class MovimentacaoFilter(django_filters.FilterSet):
    """Filtro para Movimentações (Receitas e Despesas)"""
    
    # Filtro por parceiro
    parceiros = django_filters.CharFilter(
        field_name='parceiros__nome',
        lookup_expr='icontains',
        label='Parceiro',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por parceiro...'
        })
    )
    
    # Filtro por categoria
    categoria = django_filters.CharFilter(
        field_name='categoria__nome',
        lookup_expr='icontains',
        label='Categoria',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por categoria...'
        })
    )
    
    # Filtro por fazenda
    fazenda = django_filters.CharFilter(
        field_name='fazenda__nome',
        lookup_expr='icontains',
        label='Fazenda',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por fazenda...'
        })
    )
    
    # Filtro por parcelas (vista ou parcelado)
    parcelas_tipo = django_filters.ChoiceFilter(
        field_name='parcelas',
        choices=[
            ('1', 'À Vista'),
            ('2+', 'Parcelado'),
        ],
        label='Tipo de Pagamento',
        method='filter_parcelas_tipo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro por imposto de renda (apenas para receitas)
    imposto_renda = django_filters.BooleanFilter(
        field_name='imposto_renda',
        label='Com IR',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Filtro por data
    data_inicio = django_filters.DateFilter(
        field_name='data',
        lookup_expr='gte',
        label='Data Início',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    data_fim = django_filters.DateFilter(
        field_name='data',
        lookup_expr='lte',
        label='Data Fim',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Movimentacao
        fields = ['parceiros', 'categoria', 'fazenda', 'parcelas_tipo', 'imposto_renda', 'data_inicio', 'data_fim']
    
    def filter_parcelas_tipo(self, queryset, name, value):
        """Filtra por tipo de parcela (vista ou parcelado)"""
        if value == '1':
            return queryset.filter(parcelas=1)
        elif value == '2+':
            return queryset.filter(parcelas__gt=1)
        return queryset


class ParcelaFilter(django_filters.FilterSet):
    """Filtro para Parcelas"""
    
    # Filtro por parceiro
    parceiro = django_filters.CharFilter(
        field_name='movimentacao__parceiros__nome',
        lookup_expr='icontains',
        label='Parceiro',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por parceiro...'
        })
    )
    
    # Filtro por categoria
    categoria = django_filters.CharFilter(
        field_name='movimentacao__categoria__nome',
        lookup_expr='icontains',
        label='Categoria',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por categoria...'
        })
    )
    
    # Filtro por status
    status_pagamento = django_filters.ChoiceFilter(
        field_name='status_pagamento',
        choices=[
            ('Pendente', 'Pendente'),
            ('Pago', 'Pago/Recebido'),
        ],
        label='Status',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro por data de vencimento
    vencimento_inicio = django_filters.DateFilter(
        field_name='data_vencimento',
        lookup_expr='gte',
        label='Vencimento Início',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    vencimento_fim = django_filters.DateFilter(
        field_name='data_vencimento',
        lookup_expr='lte',
        label='Vencimento Fim',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = Parcela
        fields = ['parceiro', 'categoria', 'status_pagamento', 'vencimento_inicio', 'vencimento_fim']
