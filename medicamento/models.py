from django.db import models
from datetime import date
from django.contrib.auth.models import User
from perfis.models import Fazenda


class Medicamento(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Medicamento")
    fazenda = models.ForeignKey(
        Fazenda, on_delete=models.CASCADE, verbose_name="Fazenda"
    )

    def __str__(self):
        return f"{self.nome}"

    @property
    def proxima_validade(self):
        """
        Retorna a validade mais próxima (a primeira a vencer) entre as entradas.
        Se não houver entradas, retorna None.
        """
        entrada = self.entradamedicamento_set.order_by("validade").first()
        return entrada.validade if entrada else None

    @property
    def quantidade_total(self):
        """
        Calcula o estoque atual: entradas - saídas.
        """
        entradas = sum(e.quantidade for e in self.entradamedicamento_set.all())
        saidas = sum(s.quantidade for s in self.saidamedicamento_set.all())
        return entradas - saidas

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"
        ordering = ["nome"]


class EntradaMedicamento(models.Model):
    medicamento = models.ForeignKey(
        Medicamento, on_delete=models.CASCADE, verbose_name="Medicamento"
    )
    valor_medicamento = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Total"
    )
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade Adicionada")
    quantidade_disponivel = models.PositiveIntegerField(
        verbose_name="Quantidade Disponível",
        help_text="Quantidade atual disponível (descontando saídas)",
        default=0
    )
    validade = models.DateField(verbose_name="Data de Validade")
    cadastrada_por = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Cadastrado Por"
    )
    data_cadastro = models.DateTimeField(
        auto_now_add=True, verbose_name="Data de Cadastro"
    )
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação")

    def save(self, *args, **kwargs):
        # Se é nova entrada, quantidade_disponivel = quantidade
        if not self.pk:
            self.quantidade_disponivel = self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medicamento.nome} - {self.quantidade_disponivel}/{self.quantidade} un. - Validade: {self.validade}"

    class Meta:
        verbose_name = "Entrada de Medicamento"
        verbose_name_plural = "Entradas de Medicamentos"
        ordering = ["validade"]
        indexes = [
            models.Index(fields=['validade']),
            models.Index(fields=['validade', 'quantidade_disponivel']),
            models.Index(fields=['medicamento', 'validade']),
            models.Index(fields=['-data_cadastro']),
        ]


class SaidaMedicamento(models.Model):
    medicamento = models.ForeignKey(
        Medicamento, on_delete=models.CASCADE, verbose_name="Medicamento"
    )
    entrada = models.ForeignKey(
        EntradaMedicamento, 
        on_delete=models.CASCADE, 
        verbose_name="Entrada Origem",
        help_text="Entrada da qual foi dada a saída"
    )
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade Removida")
    motivo = models.TextField(blank=True, null=True, verbose_name="Motivo da Saída")
    registrada_por = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Registrado Por"
    )
    data_saida = models.DateTimeField(
        auto_now_add=True, verbose_name="Data da Saída"
    )

    def __str__(self):
        return f"Saída: {self.medicamento.nome} - {self.quantidade} un. (Entrada #{self.entrada.id})"

    class Meta:
        verbose_name = "Saída de Medicamento"
        verbose_name_plural = "Saídas de Medicamentos"
        ordering = ["-data_saida"]
