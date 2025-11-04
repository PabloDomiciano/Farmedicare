from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta, datetime
from decimal import Decimal
import pytz

from medicamento.models import Medicamento, EntradaMedicamento, SaidaMedicamento
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
        
        # Verificar fazenda ativa
        fazenda_ativa = self.request.fazenda_ativa if hasattr(self.request, 'fazenda_ativa') else None
        if not fazenda_ativa:
            # Retornar contexto vazio se não há fazenda ativa
            context['error'] = 'Nenhuma fazenda selecionada'
            return context
        
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
        
        # Receitas - OTIMIZADO com select_related - FILTRANDO POR FAZENDA
        receitas = Movimentacao.objects.filter(
            fazenda=fazenda_ativa,
            categoria__tipo='receita',
            data__range=[data_inicio, data_fim]
        ).select_related('categoria', 'fazenda', 'parceiros')
        
        total_receitas = receitas.aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        count_receitas = receitas.count()
        
        # Despesas - OTIMIZADO - FILTRANDO POR FAZENDA
        despesas = Movimentacao.objects.filter(
            fazenda=fazenda_ativa,
            categoria__tipo='despesa',
            data__range=[data_inicio, data_fim]
        ).select_related('categoria', 'fazenda', 'parceiros')
        
        total_despesas = despesas.aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        count_despesas = despesas.count()
        
        # Saldo
        saldo = total_receitas - total_despesas
        
        # Parcelas pendentes - OTIMIZADO - FILTRANDO POR FAZENDA
        parcelas_pendentes = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            data_vencimento__range=[data_inicio, data_fim]
        ).exclude(status_pagamento='Pago').select_related('movimentacao')
        
        total_pendente = parcelas_pendentes.aggregate(
            total=Sum('valor_parcela')
        )['total'] or Decimal('0.00')
        
        # Parcelas pagas - OTIMIZADO - FILTRANDO POR FAZENDA
        parcelas_pagas = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            data_quitacao__range=[data_inicio, data_fim],
            status_pagamento='Pago'
        ).select_related('movimentacao')
        
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
        
        # OTIMIZADO: Total de UNIDADES em estoque (soma de quantidade_disponivel) - FILTRANDO POR FAZENDA
        # Igual à página de estoque de medicamentos
        total_unidades_estoque = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            quantidade_disponivel__gt=0
        ).aggregate(
            total=Sum('quantidade_disponivel')
        )['total'] or 0
        
        # OTIMIZADO: Calcular medicamentos com estoque baixo (< 10 unidades por medicamento) - FILTRANDO POR FAZENDA
        estoques_por_medicamento = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa
        ).values(
            'medicamento'
        ).annotate(
            total_estoque=Sum('quantidade_disponivel')
        ).filter(total_estoque__gt=0, total_estoque__lt=10)
        
        medicamentos_baixo_estoque = estoques_por_medicamento.count()
        
        # Entradas no período - OTIMIZADO com only() - FILTRANDO POR FAZENDA
        entradas = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            data_cadastro__range=[data_inicio, data_fim]
        ).only('id', 'quantidade', 'valor_medicamento', 'medicamento_id')
        
        total_entradas = entradas.count()
        
        # Valor total = soma de todos os valores (já calculados no cadastro)
        valor_total_estoque = entradas.aggregate(
            total=Sum('valor_medicamento')
        )['total'] or Decimal('0.00')
        
        # Medicamentos próximos ao vencimento (30 dias) - OTIMIZADO - FILTRANDO POR FAZENDA
        data_vencimento_limite = hoje + timedelta(days=30)
        
        medicamentos_vencer = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            validade__lte=data_vencimento_limite,
            validade__gte=hoje,
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Medicamentos vencidos - OTIMIZADO - FILTRANDO POR FAZENDA
        medicamentos_vencidos = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            validade__lt=hoje,
            quantidade_disponivel__gt=0
        ).only('id').count()
        
        # Converter datas para datetime aware para filtros de DateTimeField
        data_inicio_datetime = timezone.make_aware(datetime.combine(data_inicio, datetime.min.time()))
        data_fim_datetime = timezone.make_aware(datetime.combine(data_fim, datetime.max.time()))
        
        # Top 5 medicamentos mais movimentados (baseado em SAÍDAS) - OTIMIZADO com only()
        top_medicamentos = SaidaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            data_saida__gte=data_inicio_datetime,
            data_saida__lte=data_fim_datetime
        ).values(
            'medicamento__nome',
            'medicamento__fazenda__nome'
        ).annotate(
            quantidade_total=Sum('quantidade')
        ).order_by('-quantidade_total')[:5]
        
        # ========== NOTIFICAÇÕES DE MOVIMENTAÇÕES ==========
        
        # Parcelas vencidas (receitas e despesas) - OTIMIZADO - FILTRANDO POR FAZENDA
        data_limite_vencimento = hoje + timedelta(days=5)
        
        parcelas_vencidas = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            data_vencimento__lt=hoje,
            status_pagamento__in=['Pendente', 'Atrasado']
        ).select_related('movimentacao__categoria')
        
        parcelas_vencer_5dias = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            data_vencimento__gte=hoje,
            data_vencimento__lte=data_limite_vencimento,
            status_pagamento__in=['Pendente', 'Atrasado']
        ).select_related('movimentacao__categoria')
        
        # Separar por tipo (em Python, evitando queries extras)
        parcelas_vencidas_list = list(parcelas_vencidas)
        parcelas_vencer_list = list(parcelas_vencer_5dias)
        
        receitas_vencidas = [p for p in parcelas_vencidas_list if p.movimentacao.categoria.tipo == 'receita']
        despesas_vencidas = [p for p in parcelas_vencidas_list if p.movimentacao.categoria.tipo == 'despesa']
        receitas_vencer = [p for p in parcelas_vencer_list if p.movimentacao.categoria.tipo == 'receita']
        despesas_vencer = [p for p in parcelas_vencer_list if p.movimentacao.categoria.tipo == 'despesa']
        
        # ========== DADOS PARA GRÁFICOS ==========
        
        # OTIMIZADO: Gráfico comparativo usando UMA query + processamento em Python + CACHE - FILTRANDO POR FAZENDA
        # Buscar últimos 6 meses de dados (iniciar 6 meses atrás)
        inicio_6_meses = (hoje - timedelta(days=180)).replace(day=1)
        cache_key = f'grafico_comparativo_6meses_{inicio_6_meses}_fazenda_{fazenda_ativa.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            comparativo_labels = cached_data['labels']
            comparativo_receitas = cached_data['receitas']
            comparativo_despesas = cached_data['despesas']
        else:
            # Uma única query para todas as movimentações dos últimos 6 meses - FILTRANDO POR FAZENDA
            from django.db.models.functions import TruncMonth
            movimentacoes_mensais = Movimentacao.objects.filter(
                fazenda=fazenda_ativa,
                data__gte=inicio_6_meses
            ).annotate(
                mes=TruncMonth('data')
            ).values('mes', 'categoria__tipo').annotate(
                total=Sum('valor_total')
            ).order_by('mes', 'categoria__tipo')
            
            # Preparar estrutura dos últimos 6 meses
            comparativo_labels = []
            comparativo_receitas = []
            comparativo_despesas = []
            
            # Criar dicionário para facilitar lookup
            dados_por_mes = {}
            for mov in movimentacoes_mensais:
                mes_key = mov['mes'].strftime('%Y-%m')
                if mes_key not in dados_por_mes:
                    dados_por_mes[mes_key] = {'receita': 0, 'despesa': 0}
                
                tipo = mov['categoria__tipo']
                valor = float(mov['total'] or 0)
                dados_por_mes[mes_key][tipo] = valor
            
            # Preencher arrays dos últimos 6 meses
            for i in range(5, -1, -1):
                data_ref = hoje - timedelta(days=30*i)
                mes_key = data_ref.strftime('%Y-%m')
                mes_label = data_ref.strftime('%b/%y')
                
                comparativo_labels.append(mes_label)
                comparativo_receitas.append(dados_por_mes.get(mes_key, {}).get('receita', 0))
                comparativo_despesas.append(dados_por_mes.get(mes_key, {}).get('despesa', 0))
            
            # Guardar no cache por 5 minutos (300 segundos)
            cache.set(cache_key, {
                'labels': comparativo_labels,
                'receitas': comparativo_receitas,
                'despesas': comparativo_despesas
            }, 300)
        
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
            'total_medicamentos': total_unidades_estoque,  # Total de UNIDADES em estoque (ex: 86)
            'total_entradas': total_entradas,
            'valor_total_estoque': valor_total_estoque,
            'medicamentos_baixo_estoque': medicamentos_baixo_estoque,
            'medicamentos_vencer': medicamentos_vencer,
            'medicamentos_vencidos': medicamentos_vencidos,
            'top_medicamentos': top_medicamentos,
            
            # Notificações de parcelas (não sobrescrever notificacoes_count do context processor)
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
    """Gera PDF completo e detalhado do relatório - FILTRADO POR FAZENDA"""
    
    # Obter fazenda ativa
    fazenda_ativa = request.fazenda_ativa if hasattr(request, 'fazenda_ativa') else None
    
    if not fazenda_ativa:
        return HttpResponseForbidden("Selecione uma fazenda antes de gerar o relatório.")
    
    # Parâmetros de filtro
    periodo = request.GET.get('periodo', '30')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Definir datas
    hoje = timezone.now().date()
    
    if data_inicio and data_fim:
        data_inicio_date = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        data_fim_date = datetime.strptime(data_fim, '%Y-%m-%d').date()
    else:
        dias = int(periodo)
        data_inicio_date = hoje - timedelta(days=dias)
        data_fim_date = hoje
    
    # Converter para datetime aware para filtros de DateTimeField
    data_inicio_datetime = timezone.make_aware(datetime.combine(data_inicio_date, datetime.min.time()))
    data_fim_datetime = timezone.make_aware(datetime.combine(data_fim_date, datetime.max.time()))
    
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
    elements.append(Paragraph(f"Fazenda: {fazenda_ativa.nome}", subheading_style))
    elements.append(Paragraph(
        f"Período: {data_inicio_date.strftime('%d/%m/%Y')} até {data_fim_date.strftime('%d/%m/%Y')}", 
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
    
    # FILTRAR POR FAZENDA
    receitas = Movimentacao.objects.filter(
        fazenda=fazenda_ativa,
        categoria__tipo='receita', 
        data__range=[data_inicio_date, data_fim_date]
    )
    despesas = Movimentacao.objects.filter(
        fazenda=fazenda_ativa,
        categoria__tipo='despesa', 
        data__range=[data_inicio_date, data_fim_date]
    )
    
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
    
    # Estatísticas gerais - FILTRADO POR FAZENDA
    total_medicamentos = Medicamento.objects.filter(fazenda=fazenda_ativa).count()
    entradas_periodo = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        data_cadastro__range=[data_inicio_datetime, data_fim_datetime]
    )
    total_entradas = entradas_periodo.count()
    
    # Calcular valor total das entradas (valor_medicamento já é o valor TOTAL da entrada)
    valor_total_entradas = entradas_periodo.aggregate(
        total=Sum('valor_medicamento')
    )['total'] or Decimal('0.00')
    
    # Medicamentos vencidos e próximos ao vencimento - FILTRADO POR FAZENDA
    trinta_dias = hoje + timedelta(days=30)
    
    medicamentos_vencidos = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__lt=hoje,
        quantidade_disponivel__gt=0
    ).count()
    
    medicamentos_vencer = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__gte=hoje,
        validade__lte=trinta_dias,
        quantidade_disponivel__gt=0
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
    
    # FILTRAR POR FAZENDA
    medicamentos = Medicamento.objects.filter(fazenda=fazenda_ativa).order_by('nome')
    
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
    
    # Medicamentos vencidos - FILTRADO POR FAZENDA
    entradas_vencidas = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__lt=hoje,
        quantidade_disponivel__gt=0
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
                str(entrada.quantidade_disponivel),
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
    
    # Medicamentos próximos ao vencimento - FILTRADO POR FAZENDA
    entradas_vencer = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__gte=hoje,
        validade__lte=trinta_dias,
        quantidade_disponivel__gt=0
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
                str(entrada.quantidade_disponivel),
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
    response['Content-Disposition'] = f'attachment; filename="relatorio_completo_{data_inicio_date.strftime("%Y%m%d")}_{data_fim_date.strftime("%Y%m%d")}.pdf"'
    
    return response


# ========== API DE NOTIFICAÇÕES ESTILO FACEBOOK ==========

def api_notificacoes(request):
    """
    API que retorna notificações detalhadas estilo Facebook
    - Parcelas de receitas vencidas ou próximas do vencimento (5 dias)
    - Parcelas de despesas vencidas ou próximas do vencimento (5 dias)
    - Medicamentos vencidos ou próximos do vencimento (30 dias)
    """
    # Obter fazenda ativa
    fazenda_ativa = request.fazenda_ativa if hasattr(request, 'fazenda_ativa') else None
    
    # Se não há fazenda ativa, retornar vazio
    if not fazenda_ativa:
        return JsonResponse({
            'total': 0,
            'notificacoes': []
        })
    
    hoje = timezone.now().date()
    data_limite_5dias = hoje + timedelta(days=5)
    data_limite_30dias = hoje + timedelta(days=30)
    
    notificacoes = []
    
    # ========== PARCELAS DE RECEITAS ==========
    
    # Receitas vencidas (não pagas) - OTIMIZADO com select_related - FILTRANDO POR FAZENDA
    receitas_vencidas = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='receita',
        data_vencimento__lt=hoje,
        status_pagamento='Pendente'
    ).select_related(
        'movimentacao__parceiros', 
        'movimentacao__categoria', 
        'movimentacao__fazenda'
    ).only(
        'id', 'ordem_parcela', 'valor_parcela', 'data_vencimento',
        'movimentacao__parcelas', 'movimentacao__descricao',
        'movimentacao__parceiros__nome',
        'movimentacao__categoria__nome',
        'movimentacao__fazenda__nome'
    )
    
    for parcela in receitas_vencidas:
        dias_atraso = (hoje - parcela.data_vencimento).days
        notificacoes.append({
            'tipo': 'receita_vencida',
            'categoria': 'vencido',
            'urgencia': 3,  # Crítico
            'icone': 'fa-hand-holding-usd',
            'cor': '#2e7d32',  # Verde escuro para receitas
            'cor_bg': '#e8f5e9',  # Fundo verde claro
            'cor_border': '#4caf50',  # Borda verde
            'titulo': f'Receita Vencida - {dias_atraso} dia(s) de atraso',
            'mensagem': f'Parcela {parcela.ordem_parcela}/{parcela.movimentacao.parcelas} vencida há {dias_atraso} dia(s)',
            'parcela_numero': parcela.ordem_parcela,
            'total_parcelas': parcela.movimentacao.parcelas,
            'valor': float(parcela.valor_parcela),
            'data_vencimento': parcela.data_vencimento.strftime('%d/%m/%Y'),
            'data_vencimento_raw': parcela.data_vencimento.isoformat(),
            'parceiro': parcela.movimentacao.parceiros.nome if parcela.movimentacao.parceiros else 'Sem parceiro',
            'categoria_nome': parcela.movimentacao.categoria.nome,
            'descricao': parcela.movimentacao.descricao or '',
            'fazenda': parcela.movimentacao.fazenda.nome,
            'id_parcela': parcela.id,
        })
    
    # Receitas a vencer (próximas 5 dias) - OTIMIZADO - FILTRANDO POR FAZENDA
    receitas_vencer = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='receita',
        data_vencimento__gte=hoje,
        data_vencimento__lte=data_limite_5dias,
        status_pagamento='Pendente'
    ).select_related(
        'movimentacao__parceiros', 
        'movimentacao__categoria', 
        'movimentacao__fazenda'
    ).only(
        'id', 'ordem_parcela', 'valor_parcela', 'data_vencimento',
        'movimentacao__parcelas', 'movimentacao__descricao',
        'movimentacao__parceiros__nome',
        'movimentacao__categoria__nome',
        'movimentacao__fazenda__nome'
    )
    
    for parcela in receitas_vencer:
        dias_restantes = (parcela.data_vencimento - hoje).days
        urgencia = 2 if dias_restantes <= 2 else 1
        categoria = 'muito_proximo' if dias_restantes <= 2 else 'proximo'
        cor = '#43a047' if dias_restantes <= 2 else '#66bb6a'  # Verde médio/claro
        
        notificacoes.append({
            'tipo': 'receita_vencer',
            'categoria': categoria,
            'urgencia': urgencia,
            'icone': 'fa-hand-holding-usd',
            'cor': cor,
            'cor_bg': '#f1f8e9',  # Fundo verde bem claro
            'cor_border': '#8bc34a',  # Borda verde claro
            'titulo': f'Receita a Vencer em {dias_restantes} dia(s)',
            'mensagem': f'Parcela {parcela.ordem_parcela}/{parcela.movimentacao.parcelas} vence em {dias_restantes} dia(s)',
            'parcela_numero': parcela.ordem_parcela,
            'total_parcelas': parcela.movimentacao.parcelas,
            'valor': float(parcela.valor_parcela),
            'data_vencimento': parcela.data_vencimento.strftime('%d/%m/%Y'),
            'data_vencimento_raw': parcela.data_vencimento.isoformat(),
            'parceiro': parcela.movimentacao.parceiros.nome if parcela.movimentacao.parceiros else 'Sem parceiro',
            'categoria_nome': parcela.movimentacao.categoria.nome,
            'descricao': parcela.movimentacao.descricao or '',
            'fazenda': parcela.movimentacao.fazenda.nome,
            'id_parcela': parcela.id,
        })
    
    # ========== PARCELAS DE DESPESAS ==========
    
    # Despesas vencidas (não pagas) - OTIMIZADO - FILTRANDO POR FAZENDA
    despesas_vencidas = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='despesa',
        data_vencimento__lt=hoje,
        status_pagamento='Pendente'
    ).select_related(
        'movimentacao__parceiros', 
        'movimentacao__categoria', 
        'movimentacao__fazenda'
    ).only(
        'id', 'ordem_parcela', 'valor_parcela', 'data_vencimento',
        'movimentacao__parcelas', 'movimentacao__descricao',
        'movimentacao__parceiros__nome',
        'movimentacao__categoria__nome',
        'movimentacao__fazenda__nome'
    )
    
    for parcela in despesas_vencidas:
        dias_atraso = (hoje - parcela.data_vencimento).days
        notificacoes.append({
            'tipo': 'despesa_vencida',
            'categoria': 'vencido',
            'urgencia': 3,  # Crítico
            'icone': 'fa-file-invoice-dollar',
            'cor': '#f57c00',  # Laranja escuro para despesas
            'cor_bg': '#fff3e0',  # Fundo laranja claro
            'cor_border': '#ff9800',  # Borda laranja
            'titulo': f'Despesa Vencida - {dias_atraso} dia(s) de atraso',
            'mensagem': f'Parcela {parcela.ordem_parcela}/{parcela.movimentacao.parcelas} vencida há {dias_atraso} dia(s)',
            'parcela_numero': parcela.ordem_parcela,
            'total_parcelas': parcela.movimentacao.parcelas,
            'valor': float(parcela.valor_parcela),
            'data_vencimento': parcela.data_vencimento.strftime('%d/%m/%Y'),
            'data_vencimento_raw': parcela.data_vencimento.isoformat(),
            'parceiro': parcela.movimentacao.parceiros.nome if parcela.movimentacao.parceiros else 'Sem parceiro',
            'categoria_nome': parcela.movimentacao.categoria.nome,
            'descricao': parcela.movimentacao.descricao or '',
            'fazenda': parcela.movimentacao.fazenda.nome,
            'id_parcela': parcela.id,
        })
    
    # Despesas a vencer (próximas 5 dias) - OTIMIZADO - FILTRANDO POR FAZENDA
    despesas_vencer = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='despesa',
        data_vencimento__gte=hoje,
        data_vencimento__lte=data_limite_5dias,
        status_pagamento='Pendente'
    ).select_related(
        'movimentacao__parceiros', 
        'movimentacao__categoria', 
        'movimentacao__fazenda'
    ).only(
        'id', 'ordem_parcela', 'valor_parcela', 'data_vencimento',
        'movimentacao__parcelas', 'movimentacao__descricao',
        'movimentacao__parceiros__nome',
        'movimentacao__categoria__nome',
        'movimentacao__fazenda__nome'
    )
    
    for parcela in despesas_vencer:
        dias_restantes = (parcela.data_vencimento - hoje).days
        urgencia = 2 if dias_restantes <= 2 else 1
        categoria = 'muito_proximo' if dias_restantes <= 2 else 'proximo'
        cor = '#fb8c00' if dias_restantes <= 2 else '#ffa726'  # Laranja médio/claro
        
        notificacoes.append({
            'tipo': 'despesa_vencer',
            'categoria': categoria,
            'urgencia': urgencia,
            'icone': 'fa-file-invoice-dollar',
            'cor': cor,
            'cor_bg': '#fff8e1',  # Fundo amarelo claro
            'cor_border': '#ffb74d',  # Borda laranja claro
            'titulo': f'Despesa a Vencer em {dias_restantes} dia(s)',
            'mensagem': f'Parcela {parcela.ordem_parcela}/{parcela.movimentacao.parcelas} vence em {dias_restantes} dia(s)',
            'parcela_numero': parcela.ordem_parcela,
            'total_parcelas': parcela.movimentacao.parcelas,
            'valor': float(parcela.valor_parcela),
            'data_vencimento': parcela.data_vencimento.strftime('%d/%m/%Y'),
            'data_vencimento_raw': parcela.data_vencimento.isoformat(),
            'parceiro': parcela.movimentacao.parceiros.nome if parcela.movimentacao.parceiros else 'Sem parceiro',
            'categoria_nome': parcela.movimentacao.categoria.nome,
            'descricao': parcela.movimentacao.descricao or '',
            'fazenda': parcela.movimentacao.fazenda.nome,
            'id_parcela': parcela.id,
        })
    
    # ========== MEDICAMENTOS ==========
    
    # Medicamentos vencidos - OTIMIZADO - FILTRANDO POR FAZENDA
    medicamentos_vencidos = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__lt=hoje,
        quantidade_disponivel__gt=0
    ).select_related('medicamento', 'medicamento__fazenda').only(
        'id', 'quantidade_disponivel', 'validade',
        'medicamento__id', 'medicamento__nome',
        'medicamento__fazenda__nome'
    )
    
    for entrada in medicamentos_vencidos:
        dias_vencido = (hoje - entrada.validade).days
        notificacoes.append({
            'tipo': 'medicamento_vencido',
            'categoria': 'vencido',
            'urgencia': 3,
            'icone': 'fa-pills',
            'cor': '#5e35b1',  # Roxo escuro para medicamentos
            'cor_bg': '#ede7f6',  # Fundo roxo claro
            'cor_border': '#7e57c2',  # Borda roxo
            'titulo': f'Medicamento Vencido há {dias_vencido} dia(s)',
            'mensagem': f'Venceu há {dias_vencido} dia(s)',
            'medicamento': entrada.medicamento.nome,
            'fazenda': entrada.medicamento.fazenda.nome,
            'lote': f'ID-{entrada.id}',
            'quantidade': entrada.quantidade_disponivel,
            'validade': entrada.validade.strftime('%d/%m/%Y'),
            'validade_raw': entrada.validade.isoformat(),
            'id_entrada': entrada.id,
        })
    
    # Medicamentos a vencer (30 dias) - OTIMIZADO - FILTRANDO POR FAZENDA
    medicamentos_vencer = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__gte=hoje,
        validade__lte=data_limite_30dias,
        quantidade_disponivel__gt=0
    ).select_related('medicamento', 'medicamento__fazenda').only(
        'id', 'quantidade_disponivel', 'validade',
        'medicamento__id', 'medicamento__nome',
        'medicamento__fazenda__nome'
    )
    
    for entrada in medicamentos_vencer:
        dias_restantes = (entrada.validade - hoje).days
        if dias_restantes <= 7:
            urgencia = 2
            categoria = 'muito_proximo'
            cor = '#7b1fa2'  # Roxo médio
        else:
            urgencia = 1
            categoria = 'proximo'
            cor = '#9c27b0'  # Roxo claro
        
        notificacoes.append({
            'tipo': 'medicamento_vencer',
            'categoria': categoria,
            'urgencia': urgencia,
            'icone': 'fa-pills',
            'cor': cor,
            'cor_bg': '#f3e5f5',  # Fundo roxo bem claro
            'cor_border': '#ab47bc',  # Borda roxo claro
            'titulo': f'Medicamento Vence em {dias_restantes} dia(s)',
            'mensagem': f'Vence em {dias_restantes} dia(s)',
            'medicamento': entrada.medicamento.nome,
            'fazenda': entrada.medicamento.fazenda.nome,
            'lote': f'ID-{entrada.id}',
            'quantidade': entrada.quantidade_disponivel,
            'validade': entrada.validade.strftime('%d/%m/%Y'),
            'validade_raw': entrada.validade.isoformat(),
            'id_entrada': entrada.id,
        })
    
    # Ordenar por urgência (3 = crítico primeiro) e depois por data
    notificacoes.sort(key=lambda x: (
        -x['urgencia'],
        x.get('data_vencimento_raw', x.get('validade_raw', ''))
    ))
    
    return JsonResponse({
        'total': len(notificacoes),
        'notificacoes': notificacoes
    })


def notificacoes_page(request):
    """
    Página completa de notificações estilo Facebook
    """
    # Obter fazenda ativa
    fazenda_ativa = request.fazenda_ativa if hasattr(request, 'fazenda_ativa') else None
    
    # Se não há fazenda ativa, retornar contadores zerados
    if not fazenda_ativa:
        context = {
            'titulo': 'Notificações',
            'title': 'Notificações - Farmedicare',
            'total': 0,
            'receitas_vencidas': 0,
            'receitas_vencer': 0,
            'despesas_vencidas': 0,
            'despesas_vencer': 0,
            'medicamentos_vencidos': 0,
            'medicamentos_vencer': 0,
        }
        return render(request, 'relatorios/notificacoes_unificadas.html', context)
    
    hoje = timezone.now().date()
    data_limite_5dias = hoje + timedelta(days=5)
    data_limite_30dias = hoje + timedelta(days=30)
    
    # Contadores OTIMIZADOS - usar only('id') para count - FILTRANDO POR FAZENDA
    receitas_vencidas = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='receita',
        data_vencimento__lt=hoje,
        status_pagamento='Pendente'
    ).only('id').count()
    
    receitas_vencer = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='receita',
        data_vencimento__gte=hoje,
        data_vencimento__lte=data_limite_5dias,
        status_pagamento='Pendente'
    ).only('id').count()
    
    despesas_vencidas = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='despesa',
        data_vencimento__lt=hoje,
        status_pagamento='Pendente'
    ).only('id').count()
    
    despesas_vencer = Parcela.objects.filter(
        movimentacao__fazenda=fazenda_ativa,
        movimentacao__categoria__tipo='despesa',
        data_vencimento__gte=hoje,
        data_vencimento__lte=data_limite_5dias,
        status_pagamento='Pendente'
    ).only('id').count()
    
    medicamentos_vencidos = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__lt=hoje,
        quantidade_disponivel__gt=0
    ).only('id').count()
    
    medicamentos_vencer = EntradaMedicamento.objects.filter(
        medicamento__fazenda=fazenda_ativa,
        validade__gte=hoje,
        validade__lte=data_limite_30dias,
        quantidade_disponivel__gt=0
    ).only('id').count()
    
    total = (
        receitas_vencidas + receitas_vencer +
        despesas_vencidas + despesas_vencer +
        medicamentos_vencidos + medicamentos_vencer
    )
    
    context = {
        'titulo': 'Notificações',
        'title': 'Notificações - Farmedicare',
        'total': total,
        'receitas_vencidas': receitas_vencidas,
        'receitas_vencer': receitas_vencer,
        'despesas_vencidas': despesas_vencidas,
        'despesas_vencer': despesas_vencer,
        'medicamentos_vencidos': medicamentos_vencidos,
        'medicamentos_vencer': medicamentos_vencer,
    }
    
    return render(request, 'relatorios/notificacoes_unificadas.html', context)


