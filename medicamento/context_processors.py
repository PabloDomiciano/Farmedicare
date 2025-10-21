"""
Context Processors para adicionar notificações em todos os templates
"""
from medicamento.notificacoes import contar_notificacoes_nao_lidas


def notificacoes_medicamentos(request):
    """
    Adiciona o contador de notificações não lidas em todos os templates.
    """
    if request.user.is_authenticated:
        return {
            'notificacoes_count': contar_notificacoes_nao_lidas()
        }
    return {
        'notificacoes_count': 0
    }
