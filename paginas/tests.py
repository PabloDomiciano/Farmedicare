import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from paginas.views import PaginaView
from movimentacao.models import Movimentacao, Categoria
from medicamento.models import Medicamento, EntradaMedicamento
from perfis.models import Fazenda, Parceiros


class TestPaginaView(TestCase):
    """Testes da view principal (dashboard)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste')
        self.parceiro = Parceiros.objects.create(nome='Parceiro Teste')
    
    def test_pagina_index_requires_login(self):
        """Testa se a página inicial requer autenticação"""
        self.client.logout()
        url = reverse('pagina_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
    
    def test_pagina_index_renders_correct_template(self):
        """Testa se renderiza o template correto"""
        url = reverse('pagina_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
    
    def test_pagina_index_calculates_total_receitas(self):
        """Testa cálculo de total de receitas"""
        categoria = Categoria.objects.create(nome='Venda', tipo='receita')
        
        Movimentacao.objects.create(
            tipo='receita',
            parceiros=self.parceiro,
            categoria=categoria,
            valor_total=Decimal('1000.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        Movimentacao.objects.create(
            tipo='receita',
            parceiros=self.parceiro,
            categoria=categoria,
            valor_total=Decimal('500.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        self.assertEqual(response.context['total_receitas'], Decimal('1500.00'))
    
    def test_pagina_index_calculates_total_despesas(self):
        """Testa cálculo de total de despesas"""
        categoria = Categoria.objects.create(nome='Compra', tipo='despesa')
        
        Movimentacao.objects.create(
            tipo='despesa',
            parceiros=self.parceiro,
            categoria=categoria,
            valor_total=Decimal('300.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        Movimentacao.objects.create(
            tipo='despesa',
            parceiros=self.parceiro,
            categoria=categoria,
            valor_total=Decimal('200.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        self.assertEqual(response.context['total_despesas'], Decimal('500.00'))
    
    def test_pagina_index_calculates_saldo(self):
        """Testa cálculo do saldo (receitas - despesas)"""
        cat_receita = Categoria.objects.create(nome='Venda', tipo='receita')
        cat_despesa = Categoria.objects.create(nome='Compra', tipo='despesa')
        
        Movimentacao.objects.create(
            tipo='receita',
            parceiros=self.parceiro,
            categoria=cat_receita,
            valor_total=Decimal('2000.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        Movimentacao.objects.create(
            tipo='despesa',
            parceiros=self.parceiro,
            categoria=cat_despesa,
            valor_total=Decimal('800.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        self.assertEqual(response.context['saldo'], Decimal('1200.00'))
    
    def test_pagina_index_medicamento_totals(self):
        """Testa cálculo de totais de medicamentos"""
        medicamento = Medicamento.objects.create(
            nome='Paracetamol',
            fazenda=self.fazenda
        )
        
        EntradaMedicamento.objects.create(
            medicamento=medicamento,
            valor_medicamento=Decimal('150.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        EntradaMedicamento.objects.create(
            medicamento=medicamento,
            valor_medicamento=Decimal('250.00'),
            quantidade=20,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        self.assertEqual(response.context['total_quantidade'], 30)
        self.assertEqual(response.context['total_valor'], Decimal('400.00'))
    
    def test_pagina_index_with_no_data(self):
        """Testa página inicial sem dados"""
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        self.assertEqual(response.context['total_receitas'], 0)
        self.assertEqual(response.context['total_despesas'], 0)
        self.assertEqual(response.context['saldo'], 0)
        self.assertEqual(response.context['total_quantidade'], 0)
        self.assertEqual(response.context['total_valor'], 0)
    
    def test_dados_grafico_linhas(self):
        """Testa geração de dados para gráfico de linhas"""
        view = PaginaView()
        dados = view.get_dados_grafico_linhas()
        
        self.assertIn('meses', dados)
        self.assertIn('receitas', dados)
        self.assertIn('despesas', dados)
        self.assertEqual(len(dados['meses']), 6)
        self.assertEqual(len(dados['receitas']), 6)
        self.assertEqual(len(dados['despesas']), 6)
    
    def test_dados_grafico_pizza(self):
        """Testa geração de dados para gráfico de pizza"""
        view = PaginaView()
        dados = view.get_dados_grafico_pizza()
        
        self.assertIn('categorias', dados)
        self.assertIn('valores', dados)
    
    def test_dados_grafico_pizza_with_data(self):
        """Testa gráfico de pizza com dados"""
        cat_despesa = Categoria.objects.create(nome='Combustível', tipo='despesa')
        
        Movimentacao.objects.create(
            tipo='despesa',
            parceiros=self.parceiro,
            categoria=cat_despesa,
            valor_total=Decimal('500.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        view = PaginaView()
        dados = view.get_dados_grafico_pizza()
        
        self.assertIn('Combustível', dados['categorias'])
        self.assertIn(500.0, dados['valores'])
    
    def test_grafico_data_json_is_valid(self):
        """Testa se os dados JSON do gráfico são válidos"""
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        grafico_json = response.context['grafico_data_json']
        
        # Verifica se é um JSON válido
        try:
            dados = json.loads(grafico_json)
            self.assertIn('meses', dados)
            self.assertIn('receitas', dados)
            self.assertIn('despesas', dados)
            self.assertIn('categorias', dados)
            self.assertIn('valores', dados)
            self.assertIn('totais', dados)
        except json.JSONDecodeError:
            self.fail("grafico_data_json não é um JSON válido")
    
    def test_grafico_totais_structure(self):
        """Testa estrutura dos totais no JSON"""
        url = reverse('pagina_index')
        response = self.client.get(url)
        
        grafico_json = response.context['grafico_data_json']
        dados = json.loads(grafico_json)
        
        self.assertIn('totais', dados)
        self.assertIn('receitas', dados['totais'])
        self.assertIn('despesas', dados['totais'])
        self.assertIn('saldo', dados['totais'])


@pytest.mark.django_db
class TestPaginaViewIntegration:
    """Testes de integração da página principal"""
    
    def test_dashboard_with_multiple_data_sources(self, client):
        """Testa dashboard com dados de múltiplas fontes"""
        user = User.objects.create_user(username='testuser', password='test123')
        client.login(username='testuser', password='test123')
        
        fazenda = Fazenda.objects.create(nome='Fazenda')
        parceiro = Parceiros.objects.create(nome='Parceiro')
        cat_receita = Categoria.objects.create(nome='Venda', tipo='receita')
        
        # Cria movimentação
        Movimentacao.objects.create(
            tipo='receita',
            parceiros=parceiro,
            categoria=cat_receita,
            valor_total=Decimal('1000.00'),
            data=date.today(),
            fazenda=fazenda,
            cadastrada_por=user
        )
        
        # Cria medicamento
        medicamento = Medicamento.objects.create(nome='Med', fazenda=fazenda)
        EntradaMedicamento.objects.create(
            medicamento=medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=5,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=user
        )
        
        url = reverse('pagina_index')
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.context['total_receitas'] == Decimal('1000.00')
        assert response.context['total_quantidade'] == 5
