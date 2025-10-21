from datetime import datetime, timedelta, date
from django.views.generic import TemplateView
from django.db.models import Sum, Count
from movimentacao.models import Movimentacao, Parcela
from medicamento.models import EntradaMedicamento, Medicamento
import json


class PaginaView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total de receitas
        total_receitas = (
            Movimentacao.objects.filter(tipo="receita").aggregate(
                total=Sum("valor_total")
            )["total"]
            or 0
        )

        # Total de despesas
        total_despesas = (
            Movimentacao.objects.filter(tipo="despesa").aggregate(
                total=Sum("valor_total")
            )["total"]
            or 0
        )

        # Saldo (receitas - despesas)
        saldo = total_receitas - total_despesas

        # Calcular crescimento de receitas do mês atual comparado com mês anterior
        mes_atual = datetime.now().strftime("%Y-%m")
        mes_anterior = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
        
        receitas_mes_atual = (
            Movimentacao.objects.filter(tipo="receita", data__startswith=mes_atual)
            .aggregate(total=Sum("valor_total"))["total"] or 0
        )
        receitas_mes_anterior = (
            Movimentacao.objects.filter(tipo="receita", data__startswith=mes_anterior)
            .aggregate(total=Sum("valor_total"))["total"] or 1
        )
        
        crescimento_receitas = (
            ((receitas_mes_atual - receitas_mes_anterior) / receitas_mes_anterior) * 100
            if receitas_mes_anterior > 0 else 0
        )

        # Calcular crescimento de despesas do mês atual comparado com mês anterior
        despesas_mes_atual = (
            Movimentacao.objects.filter(tipo="despesa", data__startswith=mes_atual)
            .aggregate(total=Sum("valor_total"))["total"] or 0
        )
        despesas_mes_anterior = (
            Movimentacao.objects.filter(tipo="despesa", data__startswith=mes_anterior)
            .aggregate(total=Sum("valor_total"))["total"] or 1
        )
        
        crescimento_despesas = (
            ((despesas_mes_atual - despesas_mes_anterior) / despesas_mes_anterior) * 100
            if despesas_mes_anterior > 0 else 0
        )

        # Buscar as entradas de medicamentos
        entradas_medicamentos = EntradaMedicamento.objects.select_related(
            "medicamento"
        ).all()
        context["entradas_medicamentos"] = entradas_medicamentos

        total_quantidade = 0
        total_valor = 0

        for entrada in entradas_medicamentos:
            total_quantidade += entrada.quantidade
            total_valor += entrada.valor_medicamento

        # Medicamentos próximos de vencer (próximos 30 dias)
        data_limite = date.today() + timedelta(days=30)
        medicamentos_proximos_vencer = EntradaMedicamento.objects.filter(
            validade__lte=data_limite,
            validade__gte=date.today()
        ).count()

        # Contar alertas urgentes (medicamentos vencidos + próximos 7 dias)
        data_urgente = date.today() + timedelta(days=7)
        alertas_urgentes = EntradaMedicamento.objects.filter(
            validade__lte=data_urgente
        ).count()

        # Total de alertas (parcelas pendentes + medicamentos próximos de vencer)
        parcelas_pendentes = Parcela.objects.filter(status_pagamento="Pendente").count()
        total_alertas = parcelas_pendentes + medicamentos_proximos_vencer

        # Últimas receitas (3 mais recentes)
        ultimas_receitas = Movimentacao.objects.filter(tipo="receita").order_by("-data")[:3]

        # Últimas despesas (3 mais recentes)
        ultimas_despesas = Movimentacao.objects.filter(tipo="despesa").order_by("-data")[:3]

        # Medicamentos próximos de vencer para listagem (3 mais urgentes)
        medicamentos_vencimento = EntradaMedicamento.objects.select_related(
            "medicamento"
        ).filter(
            validade__gte=date.today()
        ).order_by("validade")[:3]

        context["total_quantidade"] = total_quantidade
        context["total_valor"] = total_valor
        context["total_receitas"] = total_receitas
        context["total_despesas"] = total_despesas
        context["saldo"] = saldo
        context["crescimento_receitas"] = round(crescimento_receitas, 1)
        context["crescimento_despesas"] = round(crescimento_despesas, 1)
        context["total_medicamentos"] = Medicamento.objects.count()
        context["medicamentos_proximos_vencer"] = medicamentos_proximos_vencer
        context["alertas_urgentes"] = alertas_urgentes
        context["total_alertas"] = total_alertas
        context["ultimas_receitas"] = ultimas_receitas
        context["ultimas_despesas"] = ultimas_despesas
        context["medicamentos_vencimento"] = medicamentos_vencimento
        context["today"] = date.today()

        # Dados para os gráficos
        grafico_linhas = self.get_dados_grafico_linhas()
        grafico_pizza = self.get_dados_grafico_pizza()

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

    def get_dados_grafico_linhas(self):
        # Dados dos últimos 6 meses
        meses = []
        receitas_mensais = []
        despesas_mensais = []

        for i in range(5, -1, -1):  # Últimos 6 meses em ordem cronológica
            mes = (datetime.now() - timedelta(days=30 * i)).strftime("%Y-%m")
            meses.append(mes)

            receitas = (
                Movimentacao.objects.filter(
                    tipo="receita", data__startswith=mes
                ).aggregate(total=Sum("valor_total"))["total"]
                or 0
            )

            despesas = (
                Movimentacao.objects.filter(
                    tipo="despesa", data__startswith=mes
                ).aggregate(total=Sum("valor_total"))["total"]
                or 0
            )

            receitas_mensais.append(float(receitas))
            despesas_mensais.append(float(despesas))

        return {
            "meses": meses,
            "receitas": receitas_mensais,
            "despesas": despesas_mensais,
        }

    def get_dados_grafico_pizza(self):
        # Distribuição de despesas por categoria
        categorias = (
            Movimentacao.objects.filter(tipo="despesa")
            .values("categoria__nome")
            .annotate(total=Sum("valor_total"))
            .order_by("-total")
        )

        # Se não houver dados, retornar valores vazios
        if not categorias:
            return {"categorias": [], "valores": []}

        return {
            "categorias": [
                cat["categoria__nome"] or "Sem Categoria" for cat in categorias
            ],
            "valores": [float(cat["total"] or 0) for cat in categorias],
        }
