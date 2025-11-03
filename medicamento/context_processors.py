"""
Context Processors para adicionar notificações em todos os templates
"""
from medicamento.notificacoes import contar_notificacoes_nao_lidas


def notificacoes_medicamentos(request):
    """
    Adiciona o contador de notificações não lidas em todos os templates.
    Filtra por fazenda ativa.
    """
    if request.user.is_authenticated:
        # Obter fazenda ativa do request (definida pelo middleware)
        fazenda_ativa = request.fazenda_ativa if hasattr(request, 'fazenda_ativa') else None
        
        return {
            'notificacoes_count': contar_notificacoes_nao_lidas(fazenda=fazenda_ativa)
        }
    return {
        'notificacoes_count': 0
    }
