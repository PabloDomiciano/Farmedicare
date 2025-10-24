from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

from perfis.models import Fazenda, Parceiros

# Criação das entidades Movimentação, Parcela, Categoria.


############  Movimentacao  ############
class Movimentacao(models.Model):
    tipo = models.CharField(
        max_length=50,
        choices=[
            ("receita", "Receita"),
            ("despesa", "Despesa"),
        ],
    )
    parceiros = models.ForeignKey(
        Parceiros,
        on_delete=models.CASCADE,
        verbose_name="Empresa Parceira",
    )
    categoria = models.ForeignKey(
        "Categoria", on_delete=models.CASCADE, verbose_name="Categoria da Movimentação"
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    parcelas = models.IntegerField(default=1)
    imposto_renda = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="Imposto de Renda [Sim/Não]",
    )
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    data = models.DateField(verbose_name="Data da Movimentação")
    fazenda = models.ForeignKey(
        Fazenda,
        on_delete=models.CASCADE,
        verbose_name="Fazenda",
    )
    cadastrada_por = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Cadastrado Por"
    )
    cadastrado_em = models.DateTimeField(
        auto_now_add=True, verbose_name="Cadastrado Em"
    )

    def __str__(self):
        return (
            f"Tipo: {self.tipo}\n"
            f"Parceiro: {self.parceiros}\n"
            f"Valor Total: {self.valor_total}\n"
            f"Parcelas: {self.parcelas}\n"
            f"Imposto de Renda: {'Sim' if self.imposto_renda else 'Não'}\n"
            f"Descrição: {self.descricao}\n"
            f"Data: {self.data}\n"
            f"Fazenda: {self.fazenda}\n"
            f"Cadastrada Por: {self.cadastrada_por}\n"
            f"Cadastrado Em: {self.cadastrado_em}"
        )

    def gerar_parcelas(self):
        """Gera automaticamente as parcelas baseadas na movimentação"""
        # Deleta parcelas existentes para recriar
        self.parcela_set.all().delete()

        valor_parcela = self.valor_total / self.parcelas

        for i in range(self.parcelas):
            # Calcula a data de vencimento (30 dias entre cada parcela)
            data_vencimento = self.data + timedelta(days=30 * i)

            Parcela.objects.create(
                movimentacao=self,
                ordem_parcela=i + 1,
                valor_parcela=valor_parcela,
                data_vencimento=data_vencimento,
                valor_pago=0.00,
                status_pagamento="Pendente",
                data_quitacao=None,
            )

    def save(self, *args, **kwargs):
        """Override do save para gerar parcelas automaticamente"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Se for uma nova movimentação ou o número de parcelas mudou, gera as parcelas
        if is_new or "parcelas" in kwargs.get("update_fields", []):
            self.gerar_parcelas()

    class Meta:
        verbose_name_plural = "Movimentações"
        ordering = ["-cadastrado_em"]
        unique_together = ("tipo", "parceiros", "data", "fazenda")



############  Parcela  ############
class Parcela(models.Model):
    movimentacao = models.ForeignKey(
        Movimentacao, on_delete=models.CASCADE, verbose_name="Movimentação"
    )
    ordem_parcela = models.IntegerField(verbose_name="Ordem da Parcela")
    valor_parcela = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor da Parcela"
    )
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    valor_pago = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor Pago"
    )
    status_pagamento = models.CharField(
        max_length=50,
        choices=[("Pendente", "Pendente"), ("Pago", "Pago")],
        default="Pendente",
        verbose_name="Status do Pagamento",
    )
    data_quitacao = models.DateField(
        blank=True, null=True, verbose_name="Data de Quitação"
    )

    def __str__(self):
        return (
            f"Movimentação: {self.movimentacao}\n"
            f"Ordem Parcela: {self.ordem_parcela}\n"
            f"Valor da Parcela: {self.valor_parcela}\n"
            f"Data Vencimento: {self.data_vencimento}\n"
            f"Valor Pago: {self.valor_pago}\n"
            f"Status do Pagamento: {self.status_pagamento}\n"
            f"Data Quitação: {self.data_quitacao if self.data_quitacao else 'Não Quitada'}"
        )


############  Categoria  ############
class Categoria(models.Model):
    nome = models.CharField(
        max_length=100, unique=True, verbose_name="Nome da Categoria"
    )
    tipo = models.CharField(
        max_length=50,
        choices=[
            ("receita", "Receita"),
            ("despesa", "Despesa"),
        ],
        verbose_name="Tipo da Categoria",
    )

    def __str__(self):
        return f"{self.nome} ({self.tipo})"

    class Meta:
        verbose_name_plural = "Categorias"
        ordering = ["nome"]
        unique_together = ("nome", "tipo")
