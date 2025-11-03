from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from medicamento.models import EntradaMedicamento
from movimentacao.models import Parcela


def notificacoes_count(request):
    """
    Context processor que disponibiliza o contador de notificações em todas as páginas
    OTIMIZADO: Usa only('id') para reduzir carga do banco de dados + Cache de 1 minuto
    """
    # Verificar se está em cache (válido por 60 segundos)
    cache_key = 'notificacoes_count_total'
    total_notificacoes = cache.get(cache_key)
    
    if total_notificacoes is None:
        hoje = timezone.now().date()
        
        # Medicamentos vencidos - OTIMIZADO com only('id')
        medicamentos_vencidos = EntradaMedicamento.objects.filter(
            validade__lt=hoje,
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Medicamentos a vencer (30 dias) - OTIMIZADO com only('id')
        data_limite = hoje + timedelta(days=30)
        medicamentos_vencer = EntradaMedicamento.objects.filter(
            validade__range=[hoje, data_limite],
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Parcelas vencidas e a vencer (5 dias) - OTIMIZADO com only('id')
        parcelas_vencidas = Parcela.objects.filter(
            data_vencimento__lt=hoje,
            status_pagamento='Pendente'
        ).only('id').count()
        
        data_limite_parcelas = hoje + timedelta(days=5)
        parcelas_vencer = Parcela.objects.filter(
            data_vencimento__range=[hoje, data_limite_parcelas],
            status_pagamento='Pendente'
        ).only('id').count()
        
        # Total de notificações
        total_notificacoes = (
            medicamentos_vencidos + 
            medicamentos_vencer + 
            parcelas_vencidas +
            parcelas_vencer
        )
        
        # Guardar em cache por 60 segundos
        cache.set(cache_key, total_notificacoes, 60)
    
    return {
        'notificacoes_count': total_notificacoes,
    }
