from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from medicamento.models import EntradaMedicamento
from movimentacao.models import Parcela


def notificacoes_count(request):
    """
    Context processor que disponibiliza o contador de notificações em todas as páginas
    OTIMIZADO: Usa only('id') para reduzir carga do banco de dados + Cache de 1 minuto
    FILTRADO POR FAZENDA ATIVA
    """
    # Se usuário não autenticado, retornar 0
    if not request.user.is_authenticated:
        return {'notificacoes_count': 0}
    
    # Obter fazenda ativa do request (definida pelo middleware)
    fazenda_ativa = request.fazenda_ativa if hasattr(request, 'fazenda_ativa') else None
    
    # Se não há fazenda ativa, retornar 0
    if not fazenda_ativa:
        return {'notificacoes_count': 0}
    
    # Verificar se está em cache (válido por 60 segundos) - Cache por fazenda
    cache_key = f'notificacoes_count_fazenda_{fazenda_ativa.id}'
    total_notificacoes = cache.get(cache_key)
    
    if total_notificacoes is None:
        hoje = timezone.now().date()
        
        # Medicamentos vencidos - OTIMIZADO com only('id') + FILTRADO POR FAZENDA
        medicamentos_vencidos = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            validade__lt=hoje,
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Medicamentos a vencer (30 dias) - OTIMIZADO com only('id') + FILTRADO POR FAZENDA
        data_limite = hoje + timedelta(days=30)
        medicamentos_vencer = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            validade__range=[hoje, data_limite],
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Parcelas vencidas e a vencer (5 dias) - OTIMIZADO com only('id') + FILTRADO POR FAZENDA
        parcelas_vencidas = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            data_vencimento__lt=hoje,
            status_pagamento='Pendente'
        ).only('id').count()
        
        data_limite_parcelas = hoje + timedelta(days=5)
        parcelas_vencer = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
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
        
        # Guardar em cache por 60 segundos (cache específico por fazenda)
        cache.set(cache_key, total_notificacoes, 60)
    
    return {
        'notificacoes_count': total_notificacoes,
    }
