import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from medicamento.models import Medicamento, EntradaMedicamento
from perfis.models import Fazenda


class TestMedicamentoModel(TestCase):
    """Testes do modelo Medicamento"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste', cidade='São Paulo')
        self.medicamento = Medicamento.objects.create(
            nome='Paracetamol',
            fazenda=self.fazenda
        )
    
    def test_medicamento_creation(self):
        """Testa criação de um medicamento"""
        self.assertEqual(self.medicamento.nome, 'Paracetamol')
        self.assertEqual(self.medicamento.fazenda, self.fazenda)
    
    def test_medicamento_str_method(self):
        """Testa o método __str__ do modelo"""
        self.assertEqual(str(self.medicamento), 'Paracetamol')
    
    def test_medicamento_ordering(self):
        """Testa ordenação de medicamentos por nome"""
        Medicamento.objects.create(nome='Aspirina', fazenda=self.fazenda)
        Medicamento.objects.create(nome='Zinco', fazenda=self.fazenda)
        medicamentos = Medicamento.objects.all()
        self.assertEqual(medicamentos[0].nome, 'Aspirina')
        self.assertEqual(medicamentos[2].nome, 'Zinco')
    
    def test_proxima_validade_without_entradas(self):
        """Testa propriedade proxima_validade sem entradas"""
        self.assertIsNone(self.medicamento.proxima_validade)
    
    def test_proxima_validade_with_entradas(self):
        """Testa propriedade proxima_validade com entradas"""
        hoje = date.today()
        validade1 = hoje + timedelta(days=365)
        validade2 = hoje + timedelta(days=180)
        
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=validade1,
            cadastrada_por=self.user
        )
        
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('150.00'),
            quantidade=20,
            validade=validade2,
            cadastrada_por=self.user
        )
        
        # Deve retornar a validade mais próxima (180 dias)
        self.assertEqual(self.medicamento.proxima_validade, validade2)
    
    def test_quantidade_total_without_entradas(self):
        """Testa propriedade quantidade_total sem entradas"""
        self.assertEqual(self.medicamento.quantidade_total, 0)
    
    def test_quantidade_total_with_entradas(self):
        """Testa propriedade quantidade_total com múltiplas entradas"""
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('150.00'),
            quantidade=20,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        self.assertEqual(self.medicamento.quantidade_total, 30)


class TestEntradaMedicamentoModel(TestCase):
    """Testes do modelo EntradaMedicamento"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste', cidade='São Paulo')
        self.medicamento = Medicamento.objects.create(
            nome='Paracetamol',
            fazenda=self.fazenda
        )
        self.entrada = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('250.50'),
            quantidade=50,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user,
            observacao='Lote ABC123'
        )
    
    def test_entrada_creation(self):
        """Testa criação de uma entrada"""
        self.assertEqual(self.entrada.medicamento, self.medicamento)
        self.assertEqual(self.entrada.valor_medicamento, Decimal('250.50'))
        self.assertEqual(self.entrada.quantidade, 50)
        self.assertEqual(self.entrada.observacao, 'Lote ABC123')
    
    def test_entrada_str_method(self):
        """Testa o método __str__ do modelo"""
        expected = f"Paracetamol - 50 un. - Validade: {self.entrada.validade}"
        self.assertEqual(str(self.entrada), expected)
    
    def test_entrada_auto_now_add(self):
        """Testa se data_cadastro é preenchida automaticamente"""
        self.assertIsNotNone(self.entrada.data_cadastro)
    
    def test_entrada_ordering(self):
        """Testa ordenação de entradas por validade"""
        entrada1 = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=30),
            cadastrada_por=self.user
        )
        
        entrada2 = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=60),
            cadastrada_por=self.user
        )
        
        entradas = EntradaMedicamento.objects.all()
        self.assertEqual(entradas[0], entrada1)  # Validade mais próxima primeiro


class TestMedicamentoViews(TestCase):
    """Testes das views de Medicamento"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste')
    
    def test_medicamento_create_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        url = reverse('cadastro_medicamento')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
    
    def test_medicamento_create_view_get(self):
        """Testa GET na view de criação"""
        url = reverse('cadastro_medicamento')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'formularios/formulario_modelo.html')
    
    def test_medicamento_create_view_post_success(self):
        """Testa POST bem-sucedido na view de criação"""
        url = reverse('cadastro_medicamento')
        data = {
            'nome': 'Novo Medicamento',
            'fazenda': self.fazenda.id
        }
        response = self.client.post(url, data)
        
        self.assertTrue(Medicamento.objects.filter(nome='Novo Medicamento').exists())
        self.assertRedirects(response, reverse('pagina_index'))


class TestEntradaMedicamentoViews(TestCase):
    """Testes das views de EntradaMedicamento"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste')
        self.medicamento = Medicamento.objects.create(
            nome='Paracetamol',
            fazenda=self.fazenda
        )
    
    def test_entrada_create_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        url = reverse('entrada_medicamento_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
    
    def test_entrada_create_view_post_success(self):
        """Testa POST bem-sucedido na view de criação"""
        url = reverse('entrada_medicamento_create')
        data = {
            'medicamento': self.medicamento.id,
            'valor_medicamento': '150.00',
            'quantidade': 30,
            'validade': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'cadastrada_por': self.user.id,
            'observacao': 'Teste'
        }
        response = self.client.post(url, data)
        
        self.assertTrue(EntradaMedicamento.objects.filter(
            medicamento=self.medicamento,
            quantidade=30
        ).exists())
    
    def test_entrada_list_view(self):
        """Testa view de listagem de entradas"""
        url = reverse('medicamento_entradas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'medicamento_estoque.html')
    
    def test_entrada_list_view_context_totals(self):
        """Testa se os totais são calculados corretamente no contexto"""
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('200.00'),
            quantidade=20,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        url = reverse('medicamento_entradas')
        response = self.client.get(url)
        
        self.assertEqual(response.context['total_quantidade'], 30)
        self.assertEqual(response.context['total_valor'], Decimal('300.00'))
    
    def test_entrada_update_view(self):
        """Testa view de atualização de entrada"""
        entrada = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        url = reverse('editar_medicamento', kwargs={'pk': entrada.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_entrada_delete_view(self):
        """Testa view de exclusão de entrada"""
        entrada = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        url = reverse('excluir_medicamento', kwargs={'pk': entrada.pk})
        response = self.client.post(url)
        
        self.assertFalse(EntradaMedicamento.objects.filter(pk=entrada.pk).exists())
        self.assertRedirects(response, reverse('medicamento_estoque'))


@pytest.mark.django_db
class TestMedicamentoIntegration:
    """Testes de integração para Medicamento"""
    
    def test_medicamento_cascade_delete(self):
        """Testa se exclusão de medicamento exclui entradas em cascata"""
        user = User.objects.create_user(username='testuser', password='test123')
        fazenda = Fazenda.objects.create(nome='Fazenda Teste')
        medicamento = Medicamento.objects.create(nome='Teste', fazenda=fazenda)
        
        entrada = EntradaMedicamento.objects.create(
            medicamento=medicamento,
            valor_medicamento=Decimal('100.00'),
            quantidade=10,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=user
        )
        
        entrada_id = entrada.id
        medicamento.delete()
        
        # Verifica se a entrada foi excluída
        assert not EntradaMedicamento.objects.filter(id=entrada_id).exists()
