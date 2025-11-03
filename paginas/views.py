from datetime import datetime, timedelta, date
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from movimentacao.models import Movimentacao, Parcela
from medicamento.models import EntradaMedicamento, Medicamento
import json


class PaginaView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoje = date.today()
        fazenda_ativa = self.request.fazenda_ativa if hasattr(self.request, 'fazenda_ativa') else None
        
        if not fazenda_ativa:
            # Se não há fazenda ativa, retorna contexto vazio
            context.update({
                "total_quantidade": 0,
                "total_valor": 0,
                "total_receitas": 0,
                "total_despesas": 0,
                "saldo": 0,
                "crescimento_receitas": 0,
                "crescimento_despesas": 0,
                "total_medicamentos": 0,
                "medicamentos_proximos_vencer": 0,
                "alertas_urgentes": 0,
                "total_alertas": 0,
                "ultimas_receitas": [],
                "ultimas_despesas": [],
                "medicamentos_vencimento": [],
                "today": hoje,
                "grafico_data_json": json.dumps({
                    "meses": [],
                    "receitas": [],
                    "despesas": [],
                    "categorias": [],
                    "valores": [],
                    "totais": {"receitas": 0, "despesas": 0, "saldo": 0},
                })
            })
            return context
        
        # ========== OTIMIZAÇÃO: Uma única query para totais de receitas e despesas (FILTRANDO POR FAZENDA) ==========
        totais = Movimentacao.objects.filter(fazenda=fazenda_ativa).aggregate(
            total_receitas=Sum('valor_total', filter=Q(categoria__tipo='receita')),
            total_despesas=Sum('valor_total', filter=Q(categoria__tipo='despesa'))
        )
        
        total_receitas = totais['total_receitas'] or 0
        total_despesas = totais['total_despesas'] or 0
        saldo = total_receitas - total_despesas

        # ========== OTIMIZAÇÃO: Calcular meses uma vez ==========
        mes_atual_inicio = datetime.now().replace(day=1).date()
        mes_anterior_inicio = (mes_atual_inicio - timedelta(days=1)).replace(day=1)
        mes_atual_fim = hoje
        mes_anterior_fim = mes_atual_inicio - timedelta(days=1)
        
        # Query otimizada para receitas e despesas dos 2 meses (uma query) - FILTRANDO POR FAZENDA
        crescimento_data = Movimentacao.objects.filter(
            fazenda=fazenda_ativa,
            data__gte=mes_anterior_inicio
        ).aggregate(
            receitas_mes_atual=Sum('valor_total', filter=Q(
                categoria__tipo='receita',
                data__gte=mes_atual_inicio
            )),
            receitas_mes_anterior=Sum('valor_total', filter=Q(
                categoria__tipo='receita',
                data__gte=mes_anterior_inicio,
                data__lt=mes_atual_inicio
            )),
            despesas_mes_atual=Sum('valor_total', filter=Q(
                categoria__tipo='despesa',
                data__gte=mes_atual_inicio
            )),
            despesas_mes_anterior=Sum('valor_total', filter=Q(
                categoria__tipo='despesa',
                data__gte=mes_anterior_inicio,
                data__lt=mes_atual_inicio
            ))
        )
        
        receitas_mes_atual = crescimento_data['receitas_mes_atual'] or 0
        receitas_mes_anterior = crescimento_data['receitas_mes_anterior'] or 1
        despesas_mes_atual = crescimento_data['despesas_mes_atual'] or 0
        despesas_mes_anterior = crescimento_data['despesas_mes_anterior'] or 1
        
        crescimento_receitas = (
            ((receitas_mes_atual - receitas_mes_anterior) / receitas_mes_anterior) * 100
            if receitas_mes_anterior > 0 else 0
        )
        
        crescimento_despesas = (
            ((despesas_mes_atual - despesas_mes_anterior) / despesas_mes_anterior) * 100
            if despesas_mes_anterior > 0 else 0
        )

        # ========== OTIMIZAÇÃO: Aggregate para totais de medicamentos (uma query) - FILTRANDO POR FAZENDA ==========
        totais_medicamentos = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa
        ).aggregate(
            total_quantidade=Sum('quantidade'),
            total_valor=Sum('valor_medicamento')
        )
        
        total_quantidade = totais_medicamentos['total_quantidade'] or 0
        total_valor = totais_medicamentos['total_valor'] or 0

        # ========== OTIMIZAÇÃO: Contagens de medicamentos (uma query com agregação) - FILTRANDO POR FAZENDA ==========
        data_limite_30 = hoje + timedelta(days=30)
        data_limite_7 = hoje + timedelta(days=7)
        
        contagens_medicamentos = EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa
        ).aggregate(
            total_medicamentos=Count('id', filter=Q(quantidade_disponivel__gt=0)),
            proximos_vencer_30=Count('id', filter=Q(
                validade__lte=data_limite_30,
                validade__gte=hoje
            )),
            alertas_urgentes_7=Count('id', filter=Q(validade__lte=data_limite_7))
        )
        
        total_medicamentos_count = contagens_medicamentos['total_medicamentos']
        medicamentos_proximos_vencer = contagens_medicamentos['proximos_vencer_30']
        alertas_urgentes = contagens_medicamentos['alertas_urgentes_7']

        # ========== OTIMIZAÇÃO: Parcelas pendentes - FILTRANDO POR FAZENDA ==========
        parcelas_pendentes = Parcela.objects.filter(
            movimentacao__fazenda=fazenda_ativa,
            status_pagamento="Pendente"
        ).only('id').count()
        
        total_alertas = parcelas_pendentes + medicamentos_proximos_vencer

        # ========== OTIMIZAÇÃO: Últimas receitas e despesas - FILTRANDO POR FAZENDA ==========
        ultimas_receitas = list(Movimentacao.objects.filter(
            fazenda=fazenda_ativa,
            categoria__tipo="receita"
        ).select_related(
            'categoria', 'fazenda', 'parceiros'
        ).only(
            'id', 'valor_total', 'data', 'descricao', 'parcelas',
            'categoria__nome', 'fazenda__nome', 'parceiros__nome'
        ).order_by("-data")[:3])

        ultimas_despesas = list(Movimentacao.objects.filter(
            fazenda=fazenda_ativa,
            categoria__tipo="despesa"
        ).select_related(
            'categoria', 'fazenda', 'parceiros'
        ).only(
            'id', 'valor_total', 'data', 'descricao', 'parcelas',
            'categoria__nome', 'fazenda__nome', 'parceiros__nome'
        ).order_by("-data")[:3])

        # ========== OTIMIZAÇÃO: Medicamentos próximos de vencer - FILTRANDO POR FAZENDA ==========
        medicamentos_vencimento = list(EntradaMedicamento.objects.filter(
            medicamento__fazenda=fazenda_ativa,
            validade__gte=hoje,
            quantidade_disponivel__gt=0
        ).select_related(
            'medicamento', 'medicamento__fazenda'
        ).only(
            'id', 'validade', 'quantidade_disponivel', 'quantidade',
            'medicamento__id', 'medicamento__nome',
            'medicamento__fazenda__nome'
        ).order_by("validade")[:3])

        # Não carregar TODAS as entradas - removido para economizar memória
        # context["entradas_medicamentos"] = entradas_medicamentos

        context["total_quantidade"] = total_quantidade
        context["total_valor"] = total_valor
        context["total_receitas"] = total_receitas
        context["total_despesas"] = total_despesas
        context["saldo"] = saldo
        context["crescimento_receitas"] = round(crescimento_receitas, 1)
        context["crescimento_despesas"] = round(crescimento_despesas, 1)
        context["total_medicamentos"] = total_medicamentos_count
        context["medicamentos_proximos_vencer"] = medicamentos_proximos_vencer
        context["alertas_urgentes"] = alertas_urgentes
        context["total_alertas"] = total_alertas
        context["ultimas_receitas"] = ultimas_receitas
        context["ultimas_despesas"] = ultimas_despesas
        context["medicamentos_vencimento"] = medicamentos_vencimento
        context["today"] = hoje

        # Dados para os gráficos - PASSANDO FAZENDA
        grafico_linhas = self.get_dados_grafico_linhas(fazenda_ativa)
        grafico_pizza = self.get_dados_grafico_pizza(fazenda_ativa)

        context["grafico_receitas_despesas"] = grafico_linhas
        context["grafico_categorias"] = grafico_pizza

        # Passar dados para JavaScript (serializados como JSON)
        context["grafico_data_json"] = json.dumps(
            {
                "meses": grafico_linhas["meses"],
                "receitas": grafico_linhas["receitas"],
                "despesas": grafico_linhas["despesas"],
                "categorias": grafico_pizza["categorias"],
                "valores": grafico_pizza["valores"],
                "totais": {
                    "receitas": float(total_receitas),
                    "despesas": float(total_despesas),
                    "saldo": float(saldo),
                },
            }
        )

        return context

    def get_dados_grafico_linhas(self, fazenda):
        """
        OTIMIZADO: Busca dados dos últimos 6 meses em uma única query + Cache
        """
        # Cache específico por fazenda
        cache_key = f'grafico_linhas_6meses_fazenda_{fazenda.id if fazenda else "none"}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Se não há fazenda, retornar vazio
        if not fazenda:
            return {'meses': [], 'receitas': [], 'despesas': []}
        
        # Calcular range dos últimos 6 meses
        hoje = date.today()
        inicio_periodo = (datetime.now() - timedelta(days=180)).replace(day=1).date()
        
        # Uma única query para todos os meses - FILTRANDO POR FAZENDA
        movimentacoes = list(Movimentacao.objects.filter(
            fazenda=fazenda,
            data__gte=inicio_periodo
        ).values(
            'data', 'categoria__tipo', 'valor_total'
        ))
        
        # Processar em Python (mais eficiente que 12 queries separadas)
        meses_dict = {}
        for i in range(5, -1, -1):
            mes = (datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m")
            meses_dict[mes] = {'receitas': 0, 'despesas': 0}
        
        # Agregar valores
        for mov in movimentacoes:
            mes = mov['data'].strftime("%Y-%m")
            if mes in meses_dict:
                tipo = mov['categoria__tipo']
                valor = float(mov['valor_total'] or 0)
                if tipo == 'receita':
                    meses_dict[mes]['receitas'] += valor
                else:
                    meses_dict[mes]['despesas'] += valor
        
        # Preparar arrays ordenados
        meses = []
        receitas_mensais = []
        despesas_mensais = []
        
        for mes in sorted(meses_dict.keys()):
            meses.append(mes)
            receitas_mensais.append(meses_dict[mes]['receitas'])
            despesas_mensais.append(meses_dict[mes]['despesas'])

        result = {
            "meses": meses,
            "receitas": receitas_mensais,
            "despesas": despesas_mensais,
        }
        
        # Guardar no cache por 60 segundos
        cache.set(cache_key, result, 60)
        return result

    def get_dados_grafico_pizza(self, fazenda):
        """
        OTIMIZADO: Distribuição de despesas por categoria (uma query) + Cache
        """
        # Cache específico por fazenda
        cache_key = f'grafico_pizza_despesas_fazenda_{fazenda.id if fazenda else "none"}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Se não há fazenda, retornar vazio
        if not fazenda:
            return {"categorias": [], "valores": []}
        
        # FILTRANDO POR FAZENDA
        categorias = list(
            Movimentacao.objects.filter(
                fazenda=fazenda,
                categoria__tipo="despesa"
            )
            .values("categoria__nome")
            .annotate(total=Sum("valor_total"))
            .order_by("-total")
        )

        # Se não houver dados, retornar valores vazios
        if not categorias:
            return {"categorias": [], "valores": []}

        result = {
            "categorias": [
                cat["categoria__nome"] or "Sem Categoria" for cat in categorias
            ],
            "valores": [float(cat["total"] or 0) for cat in categorias],
        }
        
        # Guardar no cache por 60 segundos
        cache.set(cache_key, result, 60)
        return result

