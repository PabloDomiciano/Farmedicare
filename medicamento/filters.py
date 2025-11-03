import django_filters
from django import forms
from .models import EntradaMedicamento, Medicamento


class EntradaMedicamentoFilter(django_filters.FilterSet):
    """Filtro para Estoque de Medicamentos"""
    
    # Filtro por nome do medicamento
    medicamento_nome = django_filters.CharFilter(
        field_name='medicamento__nome',
        lookup_expr='icontains',
        label='Medicamento',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por medicamento...'
        })
    )
    
    # Filtro por fazenda
    fazenda = django_filters.CharFilter(
        field_name='medicamento__fazenda__nome',
        lookup_expr='icontains',
        label='Fazenda',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por fazenda...'
        })
    )
    
    # Filtro por status de validade
    status_validade = django_filters.ChoiceFilter(
        choices=[
            ('vencido', 'Vencido'),
            ('critico', 'Próximo a vencer (30 dias)'),
            ('atencao', 'Atenção (60 dias)'),
            ('ok', 'Válido'),
        ],
        label='Status de Validade',
        method='filter_status_validade',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro por data de validade
    validade_inicio = django_filters.DateFilter(
        field_name='validade',
        lookup_expr='gte',
        label='Validade Início',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    validade_fim = django_filters.DateFilter(
        field_name='validade',
        lookup_expr='lte',
        label='Validade Fim',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    class Meta:
        model = EntradaMedicamento
        fields = ['medicamento_nome', 'fazenda', 'status_validade', 'validade_inicio', 'validade_fim']
    
    def filter_status_validade(self, queryset, name, value):
        """Filtra por status de validade"""
        from datetime import date, timedelta
        hoje = date.today()
        
        if value == 'vencido':
            return queryset.filter(validade__lt=hoje, quantidade_disponivel__gt=0)
        elif value == 'critico':
            return queryset.filter(
                validade__gte=hoje,
                validade__lte=hoje + timedelta(days=30),
                quantidade_disponivel__gt=0
            )
        elif value == 'atencao':
            return queryset.filter(
                validade__gt=hoje + timedelta(days=30),
                validade__lte=hoje + timedelta(days=60),
                quantidade_disponivel__gt=0
            )
        elif value == 'ok':
            return queryset.filter(
                validade__gt=hoje + timedelta(days=60),
                quantidade_disponivel__gt=0
            )
        return queryset
