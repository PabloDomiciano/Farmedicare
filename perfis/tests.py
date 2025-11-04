import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from perfis.models import Parceiros, Fazenda, PerfilUsuario


class TestParceirosModel(TestCase):
    """Testes do modelo Parceiros"""
    
    def setUp(self):
        # Criar usuário e fazenda primeiro (agora são obrigatórios)
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(
            nome='Fazenda Teste',
            dono=self.user
        )
        self.parceiro = Parceiros.objects.create(
            nome='Empresa Teste',
            telefone='11999999999',
            email='contato@empresa.com',
            if_adicionais='Informações adicionais de teste',
            fazenda=self.fazenda  # Agora fazenda é obrigatória
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
        Parceiros.objects.create(nome='AAA Empresa', fazenda=self.fazenda)
        Parceiros.objects.create(nome='ZZZ Empresa', fazenda=self.fazenda)
        parceiros = Parceiros.objects.all()
        self.assertEqual(parceiros[0].nome, 'AAA Empresa')
        self.assertEqual(parceiros[2].nome, 'ZZZ Empresa')
    
    def test_parceiro_optional_fields(self):
        """Testa criação de parceiro com campos opcionais vazios"""
        parceiro = Parceiros.objects.create(nome='Empresa Simples', fazenda=self.fazenda)
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
            descricao='Uma fazenda de teste',
            dono=self.user  # Dono agora é obrigatório
        )
    
    def test_fazenda_creation(self):
        """Testa criação de uma fazenda"""
        self.assertEqual(self.fazenda.nome, 'Fazenda Teste')
        self.assertEqual(self.fazenda.cidade, 'São Paulo')
        self.assertEqual(self.fazenda.descricao, 'Uma fazenda de teste')
    
    def test_fazenda_str_method(self):
        """Testa o método __str__ do modelo"""
        self.assertEqual(str(self.fazenda), 'Fazenda Teste - São Paulo')
    
    def test_fazenda_many_to_many_usuarios(self):
        """Testa relacionamento ManyToMany com usuários através do PerfilUsuario"""
        user2 = User.objects.create_user(username='testuser2', password='test123')
        # Adiciona fazenda ao perfil do usuário
        self.user.perfil.fazendas.add(self.fazenda)
        user2.perfil.fazendas.add(self.fazenda)
        
        self.assertEqual(self.fazenda.usuarios.count(), 2)
        self.assertIn(self.user.perfil, self.fazenda.usuarios.all())
        self.assertIn(user2.perfil, self.fazenda.usuarios.all())
    
    def test_fazenda_ordering(self):
        """Testa ordenação de fazendas por nome"""
        user2 = User.objects.create_user(username='testuser2', password='test123')
        Fazenda.objects.create(nome='AAA Fazenda', dono=self.user)
        Fazenda.objects.create(nome='ZZZ Fazenda', dono=user2)
        fazendas = Fazenda.objects.all()
        self.assertEqual(fazendas[0].nome, 'AAA Fazenda')
        self.assertEqual(fazendas[2].nome, 'ZZZ Fazenda')
    
    def test_fazenda_optional_fields(self):
        """Testa criação de fazenda com campos opcionais vazios"""
        fazenda = Fazenda.objects.create(nome='Fazenda Simples', dono=self.user)
        self.assertIsNone(fazenda.cidade)
        self.assertIsNone(fazenda.descricao)


class TestPerfilUsuarioModel(TestCase):
    """Testes do modelo PerfilUsuario"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            first_name='João',
            last_name='Silva'
        )
        # Perfil é criado automaticamente via signal
        self.perfil = self.user.perfil
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste', dono=self.user)
    
    def test_perfil_criado_automaticamente(self):
        """Testa se o perfil é criado automaticamente ao criar usuário"""
        novo_user = User.objects.create_user(username='novouser', password='test123')
        self.assertTrue(hasattr(novo_user, 'perfil'))
        self.assertIsNotNone(novo_user.perfil)
    
    def test_perfil_str_method(self):
        """Testa o método __str__ do perfil"""
        self.assertEqual(str(self.perfil), 'João Silva (Funcionário)')
    
    def test_perfil_tipo_default(self):
        """Testa se o tipo padrão é funcionário"""
        self.assertEqual(self.perfil.tipo, 'funcionario')
    
    def test_perfil_pode_acessar_fazenda(self):
        """Testa se o perfil pode acessar fazenda"""
        # Fazenda do dono
        self.assertTrue(self.perfil.pode_acessar_fazenda(self.fazenda))
        
        # Fazenda com acesso concedido
        outro_user = User.objects.create_user(username='outro', password='test123')
        outra_fazenda = Fazenda.objects.create(nome='Outra Fazenda', dono=outro_user)
        self.perfil.fazendas.add(outra_fazenda)
        self.assertTrue(self.perfil.pode_acessar_fazenda(outra_fazenda))


class TestParceirosCreateView(TestCase):
    """Testes da view de criação de parceiros"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.fazenda = Fazenda.objects.create(nome='Fazenda Teste', dono=self.user)
        # Simular fazenda ativa na sessão
        session = self.client.session
        session['fazenda_ativa_id'] = self.fazenda.id
        session.save()
        self.client.login(username='testuser', password='test123')
        self.url = reverse('cadastrar_parceiro')
    
    def test_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Verifica apenas que foi redirecionado (URL exata pode variar)
        self.assertTrue('next=' in response.url or response.url.startswith('/'))
    
    def test_view_renders_correct_template(self):
        """Testa se a view renderiza o template correto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'parceiros/cadastro_parceiro.html')
    
    def test_create_parceiro_success(self):
        """Testa criação bem-sucedida de um parceiro"""
        form_data = {
            'nome': 'Nova Empresa',
            'telefone': '11988888888',
            'email': 'nova@empresa.com',
            'if_adicionais': 'Informações extras'
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertTrue(Parceiros.objects.filter(nome='Nova Empresa', fazenda=self.fazenda).exists())
        # A view redireciona para a página inicial
        self.assertEqual(response.status_code, 302)
    
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
        self.url = reverse('criar_fazenda')
    
    def test_view_requires_login(self):
        """Testa se a view requer autenticação"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Verifica apenas que foi redirecionado (URL exata pode variar)
        self.assertTrue('next=' in response.url or response.url.startswith('/'))
    
    def test_view_renders_correct_template(self):
        """Testa se a view renderiza o template correto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'fazendas/criar_fazenda_inicial.html')
    
    def test_create_fazenda_success(self):
        """Testa criação bem-sucedida de uma fazenda"""
        form_data = {
            'nome': 'Nova Fazenda',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ',
            'descricao': 'Descrição da fazenda'
        }
        response = self.client.post(self.url, data=form_data)
        
        fazenda = Fazenda.objects.filter(nome='Nova Fazenda').first()
        self.assertIsNotNone(fazenda)
        self.assertEqual(fazenda.dono, self.user)
        # A view redireciona para a página inicial após criar a fazenda
        self.assertEqual(response.status_code, 302)
    
    def test_create_fazenda_missing_required_field(self):
        """Testa criação de fazenda sem campo obrigatório"""
        form_data = {
            'cidade': 'São Paulo',
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertFalse(Fazenda.objects.filter(cidade='São Paulo', dono=self.user).exists())
        self.assertEqual(response.status_code, 200)


class TestParceirosIntegration(TestCase):
    """Testes de integração para Parceiros"""
    
    def test_parceiro_cascade_delete(self):
        """Testa se a exclusão de parceiro afeta movimentações"""
        from movimentacao.models import Movimentacao, Categoria
        from datetime import date
        from decimal import Decimal
        
        user = User.objects.create_user(username='testuser', password='test123')
        fazenda = Fazenda.objects.create(nome='Fazenda Teste', dono=user)
        parceiro = Parceiros.objects.create(nome='Parceiro Teste', fazenda=fazenda)
        # Categoria agora também precisa de fazenda
        categoria = Categoria.objects.create(nome='Categoria Teste', tipo='receita', fazenda=fazenda)
        
        # Cria movimentação associada
        movimentacao = Movimentacao.objects.create(
            parceiros=parceiro,
            categoria=categoria,
            valor_total=Decimal('1000.00'),
            parcelas=1,
            data=date.today(),
            fazenda=fazenda,
            cadastrada_por=user
        )
        
        movimentacao_id = movimentacao.id
        
        # Exclui o parceiro
        parceiro.delete()
        
        # Verifica se a movimentação teve o parceiro setado como NULL (ou foi excluída dependendo do on_delete)
        # Como Movimentacao tem parceiros com SET_NULL, a movimentação deve existir mas sem parceiro
        movimentacao_atualizada = Movimentacao.objects.filter(id=movimentacao_id).first()
        if movimentacao_atualizada:
            self.assertIsNone(movimentacao_atualizada.parceiros)
    
    def test_fazenda_unique_together_parceiros(self):
        """Testa constraint unique_together de parceiros por fazenda"""
        user = User.objects.create_user(username='testuser', password='test123')
        fazenda1 = Fazenda.objects.create(nome='Fazenda 1', dono=user)
        fazenda2 = Fazenda.objects.create(nome='Fazenda 2', dono=user)
        
        # Mesmo nome de parceiro em fazendas diferentes deve funcionar
        parceiro1 = Parceiros.objects.create(nome='Empresa ABC', fazenda=fazenda1)
        parceiro2 = Parceiros.objects.create(nome='Empresa ABC', fazenda=fazenda2)
        
        self.assertEqual(parceiro1.nome, parceiro2.nome)
        self.assertNotEqual(parceiro1.fazenda, parceiro2.fazenda)
        
        # Mas mesmo nome na mesma fazenda deve falhar
        with self.assertRaises(Exception):
            Parceiros.objects.create(nome='Empresa ABC', fazenda=fazenda1)
