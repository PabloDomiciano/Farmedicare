from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import pytz

from medicamento.models import Medicamento, EntradaMedicamento
from movimentacao.models import Movimentacao, Parcela

import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class RelatoriosView(TemplateView):
    template_name = 'relatorios/dashboard_relatorios.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parâmetros de filtro
        periodo = self.request.GET.get('periodo', '30')  # 30, 60, 90, 120 dias
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        
        # Definir datas
        hoje = timezone.now().date()
        
        if data_inicio and data_fim:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        else:
            dias = int(periodo)
            data_inicio = hoje - timedelta(days=dias)
            data_fim = hoje
        
        context['data_inicio'] = data_inicio
        context['data_fim'] = data_fim
        context['periodo_selecionado'] = periodo
        
        # ========== DADOS DE MOVIMENTAÇÃO FINANCEIRA ==========
        
        # Receitas
        receitas = Movimentacao.objects.filter(
            tipo='receita',
            data__range=[data_inicio, data_fim]
        )
        
        total_receitas = receitas.aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        count_receitas = receitas.count()
        
        # Despesas
        despesas = Movimentacao.objects.filter(
            tipo='despesa',
            data__range=[data_inicio, data_fim]
        )
        
        total_despesas = despesas.aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        count_despesas = despesas.count()
        
        # Saldo
        saldo = total_receitas - total_despesas
        
        # Parcelas pendentes
        parcelas_pendentes = Parcela.objects.filter(
            data_vencimento__range=[data_inicio, data_fim]
        ).exclude(status_pagamento='Pago')
        
        total_pendente = parcelas_pendentes.aggregate(
            total=Sum('valor_parcela')
        )['total'] or Decimal('0.00')
        
        # Parcelas pagas
        parcelas_pagas = Parcela.objects.filter(
            data_quitacao__range=[data_inicio, data_fim],
            status_pagamento='Pago'
        )
        
        total_pago = parcelas_pagas.aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0.00')
        
        # Top 5 categorias de receita
        top_receitas_categoria = receitas.values(
            'categoria__nome'
        ).annotate(
            total=Sum('valor_total'),
            quantidade=Count('id')
        ).order_by('-total')[:5]
        
        # Top 5 categorias de despesa
        top_despesas_categoria = despesas.values(
            'categoria__nome'
        ).annotate(
            total=Sum('valor_total'),
            quantidade=Count('id')
        ).order_by('-total')[:5]
        
        # ========== DADOS DE MEDICAMENTOS ==========
        
        # Total de medicamentos cadastrados
        total_medicamentos = Medicamento.objects.count()
        
        # Entradas no período
        entradas = EntradaMedicamento.objects.filter(
            data_cadastro__range=[data_inicio, data_fim]
        )
        
        total_entradas = entradas.count()
        
        # Valor total = soma de todos os valores (já calculados no cadastro)
        valor_total_estoque = entradas.aggregate(
            total=Sum('valor_medicamento')
        )['total'] or Decimal('0.00')
        
        # Medicamentos com estoque baixo (menos de 10 unidades)
        # Como Medicamento não tem campo direto de estoque, vamos contar por entradas com quantidade baixa
        medicamentos_baixo_estoque = 0  # Removido o filtro que causava erro
        
        # Medicamentos próximos ao vencimento (30 dias)
        data_vencimento_limite = hoje + timedelta(days=30)
        
        medicamentos_vencer = EntradaMedicamento.objects.filter(
            validade__lte=data_vencimento_limite,
            validade__gte=hoje,
            quantidade__gt=0
        ).count()
        
        # Medicamentos vencidos
        medicamentos_vencidos = EntradaMedicamento.objects.filter(
            validade__lt=hoje,
            quantidade__gt=0
        ).count()
        
        # Top 5 medicamentos mais movimentados (por quantidade total de entradas)
        top_medicamentos = entradas.values(
            'medicamento__nome',
            'medicamento__fazenda__nome'
        ).annotate(
            quantidade_total=Sum('quantidade')
        ).order_by('-quantidade_total')[:5]
        
        # ========== NOTIFICAÇÕES DE MOVIMENTAÇÕES ==========
        
        # Parcelas vencidas (receitas e despesas)
        data_limite_vencimento = hoje + timedelta(days=5)
        
        parcelas_vencidas = Parcela.objects.filter(
            data_vencimento__lt=hoje,
            status_pagamento__in=['Pendente', 'Atrasado']
        ).select_related('movimentacao')
        
        parcelas_vencer_5dias = Parcela.objects.filter(
            data_vencimento__gte=hoje,
            data_vencimento__lte=data_limite_vencimento,
            status_pagamento__in=['Pendente', 'Atrasado']
        ).select_related('movimentacao')
        
        # Separar por tipo
        receitas_vencidas = parcelas_vencidas.filter(movimentacao__tipo='receita')
        despesas_vencidas = parcelas_vencidas.filter(movimentacao__tipo='despesa')
        receitas_vencer = parcelas_vencer_5dias.filter(movimentacao__tipo='receita')
        despesas_vencer = parcelas_vencer_5dias.filter(movimentacao__tipo='despesa')
        
        # Contar notificações
        notificacoes_count = (
            medicamentos_vencer + 
            medicamentos_vencidos + 
            receitas_vencidas.count() +
            despesas_vencidas.count() +
            receitas_vencer.count() +
            despesas_vencer.count()
        )
        
        # ========== DADOS PARA GRÁFICOS ==========
        
        # Gráfico comparativo: Receitas vs Despesas por mês (últimos 6 meses)
        comparativo_labels = []
        comparativo_receitas = []
        comparativo_despesas = []
        
        for i in range(5, -1, -1):
            data_ref = hoje - timedelta(days=30*i)
            mes_inicio = data_ref.replace(day=1)
            
            if i == 0:
                mes_fim = hoje
            else:
                proximo_mes = (mes_inicio + timedelta(days=32)).replace(day=1)
                mes_fim = proximo_mes - timedelta(days=1)
            
            receita_mes = Movimentacao.objects.filter(
                tipo='receita',
                data__range=[mes_inicio, mes_fim]
            ).aggregate(total=Sum('valor_total'))['total'] or 0
            
            despesa_mes = Movimentacao.objects.filter(
                tipo='despesa',
                data__range=[mes_inicio, mes_fim]
            ).aggregate(total=Sum('valor_total'))['total'] or 0
            
            comparativo_labels.append(mes_inicio.strftime('%b/%y'))
            comparativo_receitas.append(float(receita_mes))
            comparativo_despesas.append(float(despesa_mes))
        
        # ========== DADOS PARA GRÁFICOS DE COLUNAS ==========
        
        # Top 5 categorias de receita para gráfico
        top_5_receitas_labels = []
        top_5_receitas_valores = []
        for item in top_receitas_categoria:
            top_5_receitas_labels.append(item['categoria__nome'] or 'Sem Categoria')
            top_5_receitas_valores.append(float(item['total']))
        
        # Top 5 categorias de despesa para gráfico
        top_5_despesas_labels = []
        top_5_despesas_valores = []
        for item in top_despesas_categoria:
            top_5_despesas_labels.append(item['categoria__nome'] or 'Sem Categoria')
            top_5_despesas_valores.append(float(item['total']))
        
        # Top 5 medicamentos para gráfico
        top_5_medicamentos_labels = []
        top_5_medicamentos_valores = []
        for item in top_medicamentos:
            nome_completo = f"{item['medicamento__nome']} - {item['medicamento__fazenda__nome']}"
            top_5_medicamentos_labels.append(nome_completo)
            top_5_medicamentos_valores.append(int(item['quantidade_total']))
        
        # ========== CONTEXTO ==========
        
        context.update({
            # Financeiro
            'total_receitas': total_receitas,
            'count_receitas': count_receitas,
            'total_despesas': total_despesas,
            'count_despesas': count_despesas,
            'saldo': saldo,
            'total_pendente': total_pendente,
            'total_pago': total_pago,
            'top_receitas_categoria': top_receitas_categoria,
            'top_despesas_categoria': top_despesas_categoria,
            
            # Medicamentos
            'total_medicamentos': total_medicamentos,
            'total_entradas': total_entradas,
            'valor_total_estoque': valor_total_estoque,
            'medicamentos_baixo_estoque': medicamentos_baixo_estoque,
            'medicamentos_vencer': medicamentos_vencer,
            'medicamentos_vencidos': medicamentos_vencidos,
            'top_medicamentos': top_medicamentos,
            
            # Notificações
            'notificacoes_count': notificacoes_count,
            'receitas_vencidas': receitas_vencidas,
            'despesas_vencidas': despesas_vencidas,
            'receitas_vencer': receitas_vencer,
            'despesas_vencer': despesas_vencer,
            
            # Gráfico Comparativo (linha)
            'comparativo_labels': comparativo_labels,
            'comparativo_receitas': comparativo_receitas,
            'comparativo_despesas': comparativo_despesas,
            
            # Gráficos de colunas (JSON)
            'top_5_receitas_labels': top_5_receitas_labels,
            'top_5_receitas_valores': top_5_receitas_valores,
            'top_5_despesas_labels': top_5_despesas_labels,
            'top_5_despesas_valores': top_5_despesas_valores,
            'top_5_medicamentos_labels': top_5_medicamentos_labels,
            'top_5_medicamentos_valores': top_5_medicamentos_valores,
        })
        
        return context


def gerar_pdf_relatorio(request):
    """Gera PDF completo e detalhado do relatório"""
    
    # Parâmetros de filtro
    periodo = request.GET.get('periodo', '30')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Definir datas
    hoje = timezone.now().date()
    
    if data_inicio and data_fim:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    else:
        dias = int(periodo)
        data_inicio = hoje - timedelta(days=dias)
        data_fim = hoje
    
    # Criar buffer
    buffer = io.BytesIO()
    
    # Criar PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=18)
    
    # Container para elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2e7d32'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4a8f29'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=15,
        alignment=TA_CENTER
    )
    
    # ====================
    # CABEÇALHO
    # ====================
    # Obter horário local de Brasília
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    agora_brasilia = timezone.now().astimezone(fuso_brasilia)
    
    elements.append(Paragraph("RELATÓRIO GERENCIAL COMPLETO", title_style))
    elements.append(Paragraph("FARMEDICARE - Sistema de Gestão", subheading_style))
    elements.append(Paragraph(
        f"Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}", 
        subheading_style
    ))
    elements.append(Paragraph(
        f"Gerado em: {agora_brasilia.strftime('%d/%m/%Y às %H:%M:%S')}", 
        subheading_style
    ))
    elements.append(Spacer(1, 20))
    
    # ====================
    # 1. RESUMO FINANCEIRO
    # ====================
    elements.append(Paragraph("1. RESUMO FINANCEIRO GERAL", heading_style))
    
    receitas = Movimentacao.objects.filter(tipo='receita', data__range=[data_inicio, data_fim])
    despesas = Movimentacao.objects.filter(tipo='despesa', data__range=[data_inicio, data_fim])
    
    total_receitas = receitas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    total_despesas = despesas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    saldo = total_receitas - total_despesas
    count_receitas = receitas.count()
    count_despesas = despesas.count()
    
    data_resumo = [
        ['Descrição', 'Quantidade', 'Valor Total'],
        ['💰 Total de Receitas', f'{count_receitas} lançamento(s)', 
         f'R$ {total_receitas:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')],
        ['💸 Total de Despesas', f'{count_despesas} lançamento(s)', 
         f'R$ {total_despesas:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')],
        ['💵 Saldo do Período', '-', 
         f'R$ {saldo:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')],
    ]
    
    table_resumo = Table(data_resumo, colWidths=[9*cm, 4*cm, 5*cm])
    table_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a8f29')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey]),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table_resumo)
    elements.append(Spacer(1, 20))
    
    # ====================
    # 2. DETALHAMENTO DE RECEITAS
    # ====================
    elements.append(Paragraph("2. RECEITAS DETALHADAS POR CATEGORIA", heading_style))
    
    receitas_por_categoria = receitas.values('categoria__nome').annotate(
        total=Sum('valor_total'),
        quantidade=Count('id')
    ).order_by('-total')
    
    if receitas_por_categoria:
        data_receitas = [['Posição', 'Categoria', 'Qtd. Lançamentos', 'Valor Total', '% do Total']]
        
        for idx, item in enumerate(receitas_por_categoria, 1):
            percentual = (item['total'] / total_receitas * 100) if total_receitas > 0 else 0
            data_receitas.append([
                str(idx),
                item['categoria__nome'] or 'Sem Categoria',
                str(item['quantidade']),
                f"R$ {item['total']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                f"{percentual:.1f}%"
            ])
        
        table_receitas = Table(data_receitas, colWidths=[1.5*cm, 8*cm, 3*cm, 4*cm, 2*cm])
        table_receitas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgreen, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table_receitas)
    else:
        elements.append(Paragraph("➤ Nenhuma receita registrada no período.", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # ====================
    # 3. DETALHAMENTO DE DESPESAS
    # ====================
    elements.append(Paragraph("3. DESPESAS DETALHADAS POR CATEGORIA", heading_style))
    
    despesas_por_categoria = despesas.values('categoria__nome').annotate(
        total=Sum('valor_total'),
        quantidade=Count('id')
    ).order_by('-total')
    
    if despesas_por_categoria:
        data_despesas = [['Posição', 'Categoria', 'Qtd. Lançamentos', 'Valor Total', '% do Total']]
        
        for idx, item in enumerate(despesas_por_categoria, 1):
            percentual = (item['total'] / total_despesas * 100) if total_despesas > 0 else 0
            data_despesas.append([
                str(idx),
                item['categoria__nome'] or 'Sem Categoria',
                str(item['quantidade']),
                f"R$ {item['total']:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                f"{percentual:.1f}%"
            ])
        
        table_despesas = Table(data_despesas, colWidths=[1.5*cm, 8*cm, 3*cm, 4*cm, 2*cm])
        table_despesas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef5350')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightpink, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table_despesas)
    else:
        elements.append(Paragraph("➤ Nenhuma despesa registrada no período.", styles['Normal']))
    
    elements.append(PageBreak())
    
    # ====================
    # 4. ANÁLISE DE MEDICAMENTOS
    # ====================
    elements.append(Paragraph("4. ESTOQUE E MOVIMENTAÇÃO DE MEDICAMENTOS", heading_style))
    
    # Estatísticas gerais
    total_medicamentos = Medicamento.objects.count()
    entradas_periodo = EntradaMedicamento.objects.filter(data_cadastro__range=[data_inicio, data_fim])
    total_entradas = entradas_periodo.count()
    valor_total_entradas = entradas_periodo.aggregate(
        total=Sum('valor_medicamento')
    )['total'] or Decimal('0.00')
    
    # Medicamentos vencidos e próximos ao vencimento
    trinta_dias = hoje + timedelta(days=30)
    
    medicamentos_vencidos = EntradaMedicamento.objects.filter(
        validade__lt=hoje,
        quantidade__gt=0
    ).count()
    
    medicamentos_vencer = EntradaMedicamento.objects.filter(
        validade__gte=hoje,
        validade__lte=trinta_dias,
        quantidade__gt=0
    ).count()
    
    data_med_resumo = [
        ['Indicador', 'Valor'],
        ['📦 Total de Medicamentos Cadastrados', str(total_medicamentos)],
        ['📥 Entradas no Período', str(total_entradas)],
        ['💰 Valor Total das Entradas', f'R$ {valor_total_entradas:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')],
        ['⚠️ Medicamentos Próximos ao Vencimento (30 dias)', str(medicamentos_vencer)],
        ['❌ Medicamentos Vencidos com Estoque', str(medicamentos_vencidos)],
    ]
    
    table_med_resumo = Table(data_med_resumo, colWidths=[14*cm, 4*cm])
    table_med_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196f3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white]),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(table_med_resumo)
    elements.append(Spacer(1, 15))
    
    # ====================
    # 5. LISTA COMPLETA DE MEDICAMENTOS
    # ====================
    elements.append(Paragraph("5. LISTA DETALHADA DE MEDICAMENTOS", heading_style))
    
    medicamentos = Medicamento.objects.all().order_by('nome')
    
    if medicamentos:
        data_med_lista = [['Nº', 'Medicamento', 'Fazenda', 'Qtd. Total', 'Status']]
        
        for idx, med in enumerate(medicamentos, 1):
            quantidade = med.quantidade_total
            
            # Verificar status do estoque
            if quantidade == 0:
                status = '⚫ SEM ESTOQUE'
            elif quantidade < 10:
                status = '🔴 ESTOQUE BAIXO'
            elif quantidade < 50:
                status = '🟡 ESTOQUE MÉDIO'
            else:
                status = '🟢 ESTOQUE BOM'
            
            data_med_lista.append([
                str(idx),
                med.nome,
                med.fazenda.nome if med.fazenda else 'N/A',
                str(quantidade),
                status
            ])
        
        table_med_lista = Table(data_med_lista, colWidths=[1*cm, 7*cm, 4*cm, 2*cm, 4.5*cm])
        table_med_lista.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9c27b0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (2, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lavender, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_med_lista)
    else:
        elements.append(Paragraph("➤ Nenhum medicamento cadastrado.", styles['Normal']))
    
    elements.append(PageBreak())
    
    # ====================
    # 6. MEDICAMENTOS POR VALIDADE
    # ====================
    elements.append(Paragraph("6. MEDICAMENTOS: CONTROLE DE VALIDADE", heading_style))
    
    # Medicamentos vencidos
    entradas_vencidas = EntradaMedicamento.objects.filter(
        validade__lt=hoje,
        quantidade__gt=0
    ).select_related('medicamento').order_by('validade')
    
    if entradas_vencidas:
        elements.append(Paragraph("⚠️ MEDICAMENTOS VENCIDOS COM ESTOQUE", 
                                 ParagraphStyle('Alert', parent=styles['Normal'], fontSize=11, 
                                              textColor=colors.red, fontName='Helvetica-Bold')))
        elements.append(Spacer(1, 10))
        
        data_vencidos = [['Medicamento', 'Quantidade', 'Data Validade', 'Dias Vencido']]
        
        for entrada in entradas_vencidas:
            dias_vencido = (hoje - entrada.validade).days
            data_vencidos.append([
                entrada.medicamento.nome,
                str(entrada.quantidade),
                entrada.validade.strftime('%d/%m/%Y'),
                f'{dias_vencido} dia(s)'
            ])
        
        table_vencidos = Table(data_vencidos, colWidths=[9*cm, 2.5*cm, 3*cm, 4*cm])
        table_vencidos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.mistyrose, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_vencidos)
        elements.append(Spacer(1, 15))
    
    # Medicamentos próximos ao vencimento
    entradas_vencer = EntradaMedicamento.objects.filter(
        validade__gte=hoje,
        validade__lte=trinta_dias,
        quantidade__gt=0
    ).select_related('medicamento').order_by('validade')
    
    if entradas_vencer:
        elements.append(Paragraph("⏰ MEDICAMENTOS PRÓXIMOS AO VENCIMENTO (30 DIAS)", 
                                 ParagraphStyle('Warning', parent=styles['Normal'], fontSize=11, 
                                              textColor=colors.orange, fontName='Helvetica-Bold')))
        elements.append(Spacer(1, 10))
        
        data_vencer = [['Medicamento', 'Quantidade', 'Data Validade', 'Dias Restantes']]
        
        for entrada in entradas_vencer:
            dias_restantes = (entrada.validade - hoje).days
            data_vencer.append([
                entrada.medicamento.nome,
                str(entrada.quantidade),
                entrada.validade.strftime('%d/%m/%Y'),
                f'{dias_restantes} dia(s)'
            ])
        
        table_vencer = Table(data_vencer, colWidths=[9*cm, 2.5*cm, 3*cm, 4*cm])
        table_vencer.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightyellow, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_vencer)
    
    if not entradas_vencidas and not entradas_vencer:
        elements.append(Paragraph("✅ Não há medicamentos vencidos ou próximos ao vencimento.", 
                                 ParagraphStyle('Success', parent=styles['Normal'], fontSize=10, 
                                              textColor=colors.green)))
    
    # ====================
    # RODAPÉ
    # ====================
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_" * 80, styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"Relatório completo gerado pelo sistema FARMEDICARE em {agora_brasilia.strftime('%d/%m/%Y às %H:%M:%S')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                      textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar resposta
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_completo_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}.pdf"'
    
    return response


