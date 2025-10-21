from django import template
from datetime import date

register = template.Library()

@register.simple_tag
def current_date():
    """Retorna a data atual"""
    return date.today()

@register.filter
def dias_ate(data_validade):
    """Calcula quantos dias faltam até uma data"""
    if not data_validade:
        return 0
    
    hoje = date.today()
    delta = (data_validade - hoje).days
    return delta

@register.filter
def dias_ate_texto(data_validade):
    """Retorna texto formatado de dias até vencer"""
    if not data_validade:
        return "Data inválida"
    
    hoje = date.today()
    delta = (data_validade - hoje).days
    
    if delta < 0:
        return f"Vencido há {abs(delta)} dia{'s' if abs(delta) != 1 else ''}"
    elif delta == 0:
        return "Vence hoje!"
    elif delta == 1:
        return "Vence amanhã"
    elif delta <= 7:
        return f"Vence em {delta} dias (URGENTE)"
    elif delta <= 30:
        return f"Vence em {delta} dias"
    else:
        return f"Vence em {delta} dias"
