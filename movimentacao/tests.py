from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from perfis.models import Fazenda, Parceiros
from .models import Movimentacao, Categoria, Parcela

class CategoriaModelTest(TestCase):
    def setUp(self):
        self.categoria_receita = Categoria.objects.create(
            nome="Venda de Grãos",
            tipo="receita"
        )
        self.categoria_despesa = Categoria.objects.create(
            nome="Compra de Insumos",
            tipo="despesa"
        )
    
    def test_criacao_categoria(self):
        categoria = Categoria.objects.create(
            nome="Manutenção",
            tipo="despesa"
        )
        self.assertEqual(categoria.nome, "Manutenção")
        self.assertEqual(categoria.tipo, "despesa")

    def test_unique_together_nome_tipo(self):
        """Testa que não pode existir categorias com mesmo nome e tipo"""
        with self.assertRaises(Exception):
            Categoria.objects.create(
                nome="Venda de Grãos",
                tipo="receita"
            )


class MovimentacaoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.fazenda = Fazenda.objects.create(nome="Fazenda Teste")
        self.parceiro = Parceiros.objects.create(nome="Fornecedor Teste")
        self.categoria_receita = Categoria.objects.create(
            nome="Venda de Soja",
            tipo="receita"
        )
    
    def test_criacao_movimentacao_receita(self):
        movimentacao = Movimentacao.objects.create(
            tipo="receita",
            parceiros=self.parceiro,
            categoria=self.categoria_receita,
            valor_total=10000.00,
            parcelas=3,
            imposto_renda=True,
            descricao="Venda de soja safra 2024",
            data=date(2024, 1, 15),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        self.assertEqual(movimentacao.tipo, "receita")
        self.assertEqual(movimentacao.valor_total, 10000.00)
        self.assertEqual(movimentacao.parcelas, 3)
    
    def test_gerar_parcelas_automaticamente(self):
        movimentacao = Movimentacao.objects.create(
            tipo="receita",
            parceiros=self.parceiro,
            categoria=self.categoria_receita,
            valor_total=3000.00,
            parcelas=3,
            data=date(2024, 1, 1),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        parcelas = movimentacao.parcela_set.all()
        self.assertEqual(parcelas.count(), 3)
        self.assertEqual(parcelas[0].valor_parcela, 1000.00)


class ParcelaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.fazenda = Fazenda.objects.create(nome="Fazenda Teste")
        self.parceiro = Parceiros.objects.create(nome="Fornecedor Teste")
        self.categoria = Categoria.objects.create(nome="Teste", tipo="receita")
        
        self.movimentacao = Movimentacao.objects.create(
            tipo="receita",
            parceiros=self.parceiro,
            categoria=self.categoria,
            valor_total=3000.00,
            parcelas=3,
            data=date(2024, 1, 1),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
    
    def test_quitar_parcela(self):
        parcela = self.movimentacao.parcela_set.first()
        parcela.valor_pago = parcela.valor_parcela
        parcela.status_pagamento = "Pago"
        parcela.data_quitacao = date(2024, 1, 1)
        parcela.save()
        
        parcela_atualizada = Parcela.objects.get(pk=parcela.pk)
        self.assertEqual(parcela_atualizada.status_pagamento, "Pago")


from django.test import Client
from django.urls import reverse
from decimal import Decimal
from datetime import timedelta
import pytest


class TestMovimentacaoViews(TestCase):
    """Testes das views de Movimentação"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste')
        self.parceiro = Parceiros.objects.create(nome='Parceiro Teste')
        self.categoria = Categoria.objects.create(nome='Venda', tipo='receita')
    
    def test_movimentacao_create_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        url = reverse('cadastrar_movimentacao')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
    
    def test_movimentacao_receita_list_view(self):
        """Testa view de listagem de receitas"""
        Movimentacao.objects.create(
            tipo='receita',
            parceiros=self.parceiro,
            categoria=self.categoria,
            valor_total=Decimal('1000.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        url = reverse('listar_movimentacao_receita')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_receitas', response.context)
        self.assertEqual(response.context['total_receitas'], Decimal('1000.00'))
    
    def test_movimentacao_despesa_list_view(self):
        """Testa view de listagem de despesas"""
        categoria_despesa = Categoria.objects.create(nome='Despesa', tipo='despesa')
        Movimentacao.objects.create(
            tipo='despesa',
            parceiros=self.parceiro,
            categoria=categoria_despesa,
            valor_total=Decimal('500.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        url = reverse('listar_movimentacao_despesa')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_despesas', response.context)
        self.assertEqual(response.context['total_despesas'], Decimal('500.00'))
    
 