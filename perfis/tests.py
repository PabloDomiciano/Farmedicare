import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from perfis.models import Parceiros, Fazenda
from perfis.views import ParceirosCreateView, FazendaCreateView


class TestParceirosModel(TestCase):
    """Testes do modelo Parceiros"""
    
    def setUp(self):
        self.parceiro = Parceiros.objects.create(
            nome='Empresa Teste',
            telefone='11999999999',
            email='contato@empresa.com',
            if_adicionais='Informações adicionais de teste'
        )
    
    def test_parceiro_creation(self):
        """Testa criação de um parceiro"""
        self.assertEqual(self.parceiro.nome, 'Empresa Teste')
        self.assertEqual(self.parceiro.telefone, '11999999999')
        self.assertEqual(self.parceiro.email, 'contato@empresa.com')
    
    def test_parceiro_str_method(self):
        """Testa o método __str__ do modelo"""
        self.assertEqual(str(self.parceiro), 'Empresa Teste')
    
    def test_parceiro_ordering(self):
        """Testa ordenação de parceiros por nome"""
        Parceiros.objects.create(nome='AAA Empresa')
        Parceiros.objects.create(nome='ZZZ Empresa')
        parceiros = Parceiros.objects.all()
        self.assertEqual(parceiros[0].nome, 'AAA Empresa')
        self.assertEqual(parceiros[2].nome, 'ZZZ Empresa')
    
    def test_parceiro_optional_fields(self):
        """Testa criação de parceiro com campos opcionais vazios"""
        parceiro = Parceiros.objects.create(nome='Empresa Simples')
        self.assertIsNone(parceiro.telefone)
        self.assertIsNone(parceiro.email)
        self.assertIsNone(parceiro.if_adicionais)
    
    def test_parceiro_verbose_names(self):
        """Testa os verbose names dos campos"""
        self.assertEqual(
            Parceiros._meta.get_field('nome').verbose_name,
            'Nome da Empresa Parceira'
        )


class TestFazendaModel(TestCase):
    """Testes do modelo Fazenda"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(
            nome='Fazenda Teste',
            cidade='São Paulo',
            descricao='Uma fazenda de teste'
        )
        self.fazenda.usuarios.add(self.user)
    
    def test_fazenda_creation(self):
        """Testa criação de uma fazenda"""
        self.assertEqual(self.fazenda.nome, 'Fazenda Teste')
        self.assertEqual(self.fazenda.cidade, 'São Paulo')
        self.assertEqual(self.fazenda.descricao, 'Uma fazenda de teste')
    
    def test_fazenda_str_method(self):
        """Testa o método __str__ do modelo"""
        self.assertEqual(str(self.fazenda), 'Fazenda Teste - São Paulo')
    
    def test_fazenda_many_to_many_usuarios(self):
        """Testa relacionamento ManyToMany com usuários"""
        user2 = User.objects.create_user(username='testuser2', password='test123')
        self.fazenda.usuarios.add(user2)
        
        self.assertEqual(self.fazenda.usuarios.count(), 2)
        self.assertIn(self.user, self.fazenda.usuarios.all())
        self.assertIn(user2, self.fazenda.usuarios.all())
    
    def test_fazenda_ordering(self):
        """Testa ordenação de fazendas por nome"""
        Fazenda.objects.create(nome='AAA Fazenda')
        Fazenda.objects.create(nome='ZZZ Fazenda')
        fazendas = Fazenda.objects.all()
        self.assertEqual(fazendas[0].nome, 'AAA Fazenda')
        self.assertEqual(fazendas[2].nome, 'ZZZ Fazenda')
    
    def test_fazenda_optional_fields(self):
        """Testa criação de fazenda com campos opcionais vazios"""
        fazenda = Fazenda.objects.create(nome='Fazenda Simples')
        self.assertIsNone(fazenda.cidade)
        self.assertIsNone(fazenda.descricao)


class TestParceirosCreateView(TestCase):
    """Testes da view de criação de parceiros"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.url = reverse('parceiros_cadastro')
    
    def test_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/usuarios/login/', response.url)
    
    def test_view_renders_correct_template(self):
        """Testa se a view renderiza o template correto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'formulario_modelo.html')
    
    def test_create_parceiro_success(self):
        """Testa criação bem-sucedida de um parceiro"""
        form_data = {
            'nome': 'Nova Empresa',
            'telefone': '11988888888',
            'email': 'nova@empresa.com',
            'if_adicionais': 'Informações extras'
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertTrue(Parceiros.objects.filter(nome='Nova Empresa').exists())
        self.assertRedirects(response, reverse('pagina_index'))
    
    def test_create_parceiro_missing_required_field(self):
        """Testa criação de parceiro sem campo obrigatório"""
        form_data = {
            'telefone': '11988888888',
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertFalse(Parceiros.objects.filter(telefone='11988888888').exists())
        self.assertEqual(response.status_code, 200)


class TestFazendaCreateView(TestCase):
    """Testes da view de criação de fazendas"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.client.login(username='testuser', password='test123')
        self.url = reverse('fazenda_cadastro')
    
    def test_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/usuarios/login/', response.url)
    
    def test_view_renders_correct_template(self):
        """Testa se a view renderiza o template correto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'formulario_modelo.html')
    
    def test_create_fazenda_success(self):
        """Testa criação bem-sucedida de uma fazenda"""
        form_data = {
            'usuarios': [self.user.id],
            'nome': 'Nova Fazenda',
            'cidade': 'Rio de Janeiro',
            'descricao': 'Descrição da fazenda'
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertTrue(Fazenda.objects.filter(nome='Nova Fazenda').exists())
        self.assertRedirects(response, reverse('pagina_index'))
    
    def test_create_fazenda_missing_required_field(self):
        """Testa criação de fazenda sem campo obrigatório"""
        form_data = {
            'usuarios': [self.user.id],
            'cidade': 'São Paulo',
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertFalse(Fazenda.objects.filter(cidade='São Paulo').exists())
        self.assertEqual(response.status_code, 200)


@pytest.mark.django_db
class TestParceirosIntegration:
    """Testes de integração para Parceiros"""
    
    def test_parceiro_cascade_delete(self):
        """Testa se a exclusão de parceiro não quebra integridade"""
        from movimentacao.models import Movimentacao, Categoria
        from conftest import UserFactory, FazendaFactory
        
        user = UserFactory()
        fazenda = FazendaFactory()
        parceiro = Parceiros.objects.create(nome='Parceiro Teste')
        categoria = Categoria.objects.create(nome='Categoria Teste', tipo='receita')
        
        # Cria movimentação associada
        from datetime import date
        movimentacao = Movimentacao.objects.create(
            tipo='receita',
            parceiros=parceiro,
            categoria=categoria,
            valor_total=1000.00,
            data=date.today(),
            fazenda=fazenda,
            cadastrada_por=user
        )
        
        # Tenta excluir o parceiro
        parceiro_id = parceiro.id
        parceiro.delete()
        
        # Verifica se a movimentação também foi excluída (CASCADE)
        assert not Movimentacao.objects.filter(id=movimentacao.id).exists()
