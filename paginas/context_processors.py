from django.utils import timezone
from datetime import timedelta
from medicamento.models import EntradaMedicamento
from movimentacao.models import Parcela


def notificacoes_count(request):
    """
    Context processor que disponibiliza o contador de notificações em todas as páginas
    """
    hoje = timezone.now().date()
    
    # Medicamentos vencidos
    medicamentos_vencidos = EntradaMedicamento.objects.filter(
        validade__lt=hoje,
        quantidade__gt=0
    ).count()
    
    # Medicamentos a vencer (30 dias)
    data_limite = hoje + timedelta(days=30)
    medicamentos_vencer = EntradaMedicamento.objects.filter(
        validade__range=[hoje, data_limite],
        quantidade__gt=0
    ).count()
    
    # Parcelas vencidas e a vencer (5 dias)
    parcelas_vencidas = Parcela.objects.filter(
        data_vencimento__lt=hoje,
        status_pagamento='Pendente'
    ).count()
    
    data_limite_parcelas = hoje + timedelta(days=5)
    parcelas_vencer = Parcela.objects.filter(
        data_vencimento__range=[hoje, data_limite_parcelas],
        status_pagamento='Pendente'
    ).count()
    
    # Total de notificações
    total_notificacoes = (
        medicamentos_vencidos + 
        medicamentos_vencer + 
        parcelas_vencidas +
        parcelas_vencer
    )
    
    return {
        'notificacoes_count': total_notificacoes,
    }
