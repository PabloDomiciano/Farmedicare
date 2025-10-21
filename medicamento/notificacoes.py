"""
Sistema de Notificações para Controle de Validade de Medicamentos
"""
from datetime import date, timedelta
from medicamento.models import Medicamento, EntradaMedicamento


def gerar_notificacoes_medicamentos():
    """
    Gera notificações para medicamentos que estão próximos do vencimento (≤30 dias)
    ou já vencidos.
    
    Returns:
        dict: Dicionário com contadores e lista de notificações
    """
    hoje = date.today()
    limite_critico = hoje + timedelta(days=30)
    
    notificacoes = []
    vencidos = 0
    proximos_vencer = 0
    
    # Buscar todas as entradas de medicamentos
    entradas = EntradaMedicamento.objects.select_related('medicamento', 'medicamento__fazenda').order_by('validade')
    
    for entrada in entradas:
        dias_para_vencer = (entrada.validade - hoje).days
        
        # Apenas notificar se estiver vencido ou próximo (≤30 dias)
        if dias_para_vencer <= 30:
            if dias_para_vencer < 0:
                tipo = 'vencido'
                urgencia = 'critica'
                vencidos += 1
                icone = 'fa-times-circle'
                cor = '#ef5350'
                mensagem = f'<strong>{entrada.medicamento.nome}</strong> venceu há <strong>{abs(dias_para_vencer)} dias</strong>!'
            elif dias_para_vencer <= 7:
                tipo = 'muito_proximo'
                urgencia = 'alta'
                proximos_vencer += 1
                icone = 'fa-exclamation-triangle'
                cor = '#ff9800'
                mensagem = f'<strong>{entrada.medicamento.nome}</strong> vence em <strong>{dias_para_vencer} dias</strong>!'
            else:  # 8-30 dias
                tipo = 'proximo'
                urgencia = 'media'
                proximos_vencer += 1
                icone = 'fa-clock'
                cor = '#ffa726'
                mensagem = f'<strong>{entrada.medicamento.nome}</strong> vence em <strong>{dias_para_vencer} dias</strong>.'
            
            notificacoes.append({
                'tipo': tipo,
                'urgencia': urgencia,
                'icone': icone,
                'cor': cor,
                'mensagem': mensagem,
                'medicamento': entrada.medicamento.nome,
                'medicamento_id': entrada.medicamento.id,
                'entrada_id': entrada.id,
                'quantidade': entrada.quantidade,
                'validade': entrada.validade,
                'dias_para_vencer': dias_para_vencer,
                'dias_vencido_abs': abs(dias_para_vencer) if dias_para_vencer < 0 else 0,
                'fazenda': entrada.medicamento.fazenda.nome if entrada.medicamento.fazenda else '-',
                'lote': entrada.observacao if entrada.observacao else '-',
                'data_notificacao': hoje,
            })
    
    return {
        'notificacoes': notificacoes,
        'total': len(notificacoes),
        'vencidos': vencidos,
        'proximos_vencer': proximos_vencer,
        'hoje': hoje,
    }


def contar_notificacoes_nao_lidas():
    """
    Conta quantas notificações ativas existem (para o badge).
    
    Returns:
        int: Número de notificações não lidas
    """
    dados = gerar_notificacoes_medicamentos()
    return dados['total']
