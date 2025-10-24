from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='moeda_br')
def moeda_br(valor):
    """
    Formata valores monetários no padrão brasileiro
    Exemplo: 560890.88 -> 560.890,88
    """
    if valor is None:
        return '0,00'
    
    try:
        # Converter para Decimal se não for
        if not isinstance(valor, Decimal):
            valor = Decimal(str(valor))
        
        # Formatar com 2 casas decimais
        valor_str = f"{valor:.2f}"
        
        # Separar parte inteira e decimal
        partes = valor_str.split('.')
        parte_inteira = partes[0]
        parte_decimal = partes[1]
        
        # Adicionar separador de milhar
        # Inverter, adicionar pontos a cada 3 dígitos, e inverter de volta
        parte_inteira_formatada = ''
        for i, digito in enumerate(reversed(parte_inteira)):
            if i > 0 and i % 3 == 0:
                parte_inteira_formatada = '.' + parte_inteira_formatada
            parte_inteira_formatada = digito + parte_inteira_formatada
        
        # Retornar formatado
        return f"{parte_inteira_formatada},{parte_decimal}"
    
    except (ValueError, TypeError):
        return '0,00'


@register.filter(name='sum_valor_parcela')
def sum_valor_parcela(queryset):
    """
    Soma o valor_parcela de um queryset de parcelas
    """
    try:
        from django.db.models import Sum
        total = queryset.aggregate(total=Sum('valor_parcela'))['total']
        return total if total is not None else Decimal('0.00')
    except Exception:
        return Decimal('0.00')
