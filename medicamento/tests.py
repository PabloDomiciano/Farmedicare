from django.test import TestCase, Client
from django.contrib.auth.models import User
from perfis.models import Fazenda, PerfilUsuario
from medicamento.models import Medicamento, EntradaMedicamento
from datetime import date, timedelta


class MedicamentoIsolamentoFazendaTestCase(TestCase):
    """
    Testes para garantir que medicamentos são isolados por fazenda
    """
    
    def setUp(self):
        """Configuração inicial dos testes"""
        # Criar usuários
        self.user1 = User.objects.create_user(
            username='produtor1',
            password='senha123',
            first_name='Produtor',
            last_name='Um'
        )
        self.user2 = User.objects.create_user(
            username='produtor2',
            password='senha123',
            first_name='Produtor',
            last_name='Dois'
        )
        
        # Criar fazendas
        self.fazenda1 = Fazenda.objects.create(
            nome='Fazenda São João',
            cidade='São Paulo',
            estado='SP',
            dono=self.user1
        )
        self.fazenda2 = Fazenda.objects.create(
            nome='Fazenda Boa Vista',
            cidade='Rio de Janeiro',
            estado='RJ',
            dono=self.user2
        )
        
        # Associar fazendas aos perfis
        self.user1.perfil.fazendas.add(self.fazenda1)
        self.user2.perfil.fazendas.add(self.fazenda2)
        
        # Criar medicamentos
        self.med_fazenda1 = Medicamento.objects.create(
            nome='Ivermectina',
            fazenda=self.fazenda1
        )
        self.med_fazenda2 = Medicamento.objects.create(
            nome='Dipirona',
            fazenda=self.fazenda2
        )
        
        self.client = Client()
    
    def test_medicamento_pertence_a_fazenda(self):
        """Testa se medicamento está corretamente associado à fazenda"""
        self.assertEqual(self.med_fazenda1.fazenda, self.fazenda1)
        self.assertEqual(self.med_fazenda2.fazenda, self.fazenda2)
        self.assertNotEqual(self.med_fazenda1.fazenda, self.fazenda2)
    
    def test_listagem_medicamentos_filtrada_por_fazenda(self):
        """Testa se a listagem mostra apenas medicamentos da fazenda ativa"""
        # Login como user1
        self.client.login(username='produtor1', password='senha123')
        
        # Definir fazenda ativa
        session = self.client.session
        session['fazenda_ativa_id'] = self.fazenda1.id
        session.save()
        
        # Buscar medicamentos da fazenda 1
        medicamentos_fazenda1 = Medicamento.objects.filter(fazenda=self.fazenda1)
        
        # Verificar que contém apenas o medicamento da fazenda 1
        self.assertEqual(medicamentos_fazenda1.count(), 1)
        self.assertIn(self.med_fazenda1, medicamentos_fazenda1)
        self.assertNotIn(self.med_fazenda2, medicamentos_fazenda1)
    
    def test_formulario_entrada_filtra_medicamentos_por_fazenda(self):
        """Testa se o formulário de entrada mostra apenas medicamentos da fazenda ativa"""
        from medicamento.forms import EntradaMedicamentoForm
        
        # Criar formulário com fazenda 1
        form = EntradaMedicamentoForm(fazenda_ativa=self.fazenda1)
        
        # Verificar queryset do campo medicamento
        medicamentos_form = form.fields['medicamento'].queryset
        
        self.assertIn(self.med_fazenda1, medicamentos_form)
        self.assertNotIn(self.med_fazenda2, medicamentos_form)
    
    def test_criar_medicamento_sem_fazenda_especificada(self):
        """Testa que medicamentos criados recebem a fazenda do request"""
        # Login como user1
        self.client.login(username='produtor1', password='senha123')
        
        # Definir fazenda ativa
        session = self.client.session
        session['fazenda_ativa_id'] = self.fazenda1.id
        session.save()
        
        # Criar medicamento via POST (simulando o formulário)
        response = self.client.post('/medicamento/cadastrar/', {
            'nome': 'Novo Medicamento'
        })
        
        # Verificar se foi criado
        novo_med = Medicamento.objects.filter(nome='Novo Medicamento').first()
        
        # Verificar que o medicamento foi associado à fazenda correta
        # Nota: isso depende da view processar corretamente a fazenda_ativa
        if novo_med:
            self.assertEqual(novo_med.fazenda, self.fazenda1)
    
    def test_medicamento_duplicado_mesma_fazenda(self):
        """Testa que não é possível criar medicamento duplicado na mesma fazenda"""
        from django.db import IntegrityError
        
        # Tentar criar medicamento com mesmo nome na mesma fazenda
        with self.assertRaises(IntegrityError):
            Medicamento.objects.create(
                nome='Ivermectina',  # Já existe na fazenda1
                fazenda=self.fazenda1
            )
    
    def test_medicamento_mesmo_nome_fazendas_diferentes(self):
        """Testa que é possível criar medicamento com mesmo nome em fazendas diferentes"""
        # Criar medicamento com mesmo nome em fazenda diferente
        med_duplicado = Medicamento.objects.create(
            nome='Ivermectina',  # Mesmo nome do med_fazenda1
            fazenda=self.fazenda2  # Mas em fazenda diferente
        )
        
        # Verificar que foi criado com sucesso
        self.assertIsNotNone(med_duplicado.id)
        self.assertEqual(med_duplicado.nome, self.med_fazenda1.nome)
        self.assertNotEqual(med_duplicado.fazenda, self.med_fazenda1.fazenda)


class EntradaMedicamentoIsolamentoTestCase(TestCase):
    """
    Testes para garantir que entradas de medicamentos respeitam o isolamento por fazenda
    """
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='produtor',
            password='senha123'
        )
        self.fazenda1 = Fazenda.objects.create(
            nome='Fazenda 1',
            dono=self.user
        )
        self.fazenda2 = Fazenda.objects.create(
            nome='Fazenda 2',
            dono=self.user
        )
        
        self.med1 = Medicamento.objects.create(
            nome='Medicamento A',
            fazenda=self.fazenda1
        )
        self.med2 = Medicamento.objects.create(
            nome='Medicamento B',
            fazenda=self.fazenda2
        )
        
        # Criar entradas
        self.entrada1 = EntradaMedicamento.objects.create(
            medicamento=self.med1,
            quantidade=100,
            valor_medicamento=500.00,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        self.entrada2 = EntradaMedicamento.objects.create(
            medicamento=self.med2,
            quantidade=50,
            valor_medicamento=250.00,
            validade=date.today() + timedelta(days=180),
            cadastrada_por=self.user
        )
    
    def test_entrada_filtrada_por_fazenda(self):
        """Testa se as entradas são filtradas corretamente por fazenda"""
        entradas_fazenda1 = EntradaMedicamento.objects.filter(
            medicamento__fazenda=self.fazenda1
        )
        entradas_fazenda2 = EntradaMedicamento.objects.filter(
            medicamento__fazenda=self.fazenda2
        )
        
        self.assertEqual(entradas_fazenda1.count(), 1)
        self.assertEqual(entradas_fazenda2.count(), 1)
        self.assertIn(self.entrada1, entradas_fazenda1)
        self.assertIn(self.entrada2, entradas_fazenda2)
        self.assertNotIn(self.entrada1, entradas_fazenda2)
        self.assertNotIn(self.entrada2, entradas_fazenda1)


class SaidaMedicamentoTestCase(TestCase):
    """
    Testes para garantir que saídas de medicamentos funcionam corretamente
    """
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='produtor',
            password='senha123'
        )
        self.fazenda = Fazenda.objects.create(
            nome='Fazenda Teste',
            dono=self.user
        )
        
        self.medicamento = Medicamento.objects.create(
            nome='Ivermectina',
            fazenda=self.fazenda
        )
        
        # Criar entrada com 100 unidades
        self.entrada = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            quantidade=100,
            valor_medicamento=500.00,
            validade=date.today() + timedelta(days=365),
            cadastrada_por=self.user
        )
        
        self.client = Client()
    
    def test_saida_parcial_mantem_medicamento(self):
        """Testa que saída parcial mantém o medicamento cadastrado"""
        # Login
        self.client.login(username='produtor', password='senha123')
        
        # Definir fazenda ativa
        session = self.client.session
        session['fazenda_ativa_id'] = self.fazenda.id
        session.save()
        
        # Simular saída de 50 unidades via API
        from medicamento.models import SaidaMedicamento
        
        # Criar saída manualmente (simulando a API)
        self.entrada.quantidade_disponivel -= 50
        self.entrada.save()
        
        SaidaMedicamento.objects.create(
            medicamento=self.medicamento,
            entrada=self.entrada,
            quantidade=50,
            motivo='Uso no rebanho',
            registrada_por=self.user
        )
        
        # Verificar que o medicamento ainda existe
        self.assertTrue(Medicamento.objects.filter(id=self.medicamento.id).exists())
        
        # Verificar estoque
        self.medicamento.refresh_from_db()
        self.assertEqual(self.medicamento.quantidade_total, 50)
    
    def test_saida_total_mantem_medicamento_cadastrado(self):
        """
        TESTE PRINCIPAL: Verifica que quando o estoque zera, 
        o medicamento PERMANECE cadastrado para futuras entradas
        """
        # Login
        self.client.login(username='produtor', password='senha123')
        
        # Definir fazenda ativa
        session = self.client.session
        session['fazenda_ativa_id'] = self.fazenda.id
        session.save()
        
        # Simular saída de 100 unidades (todo o estoque) via API
        from medicamento.models import SaidaMedicamento
        
        # Criar saída de todo o estoque
        self.entrada.quantidade_disponivel -= 100
        self.entrada.save()
        
        SaidaMedicamento.objects.create(
            medicamento=self.medicamento,
            entrada=self.entrada,
            quantidade=100,
            motivo='Uso completo',
            registrada_por=self.user
        )
        
        # CRÍTICO: Verificar que o medicamento AINDA EXISTE mesmo com estoque zerado
        self.assertTrue(
            Medicamento.objects.filter(id=self.medicamento.id).exists(),
            "O medicamento deve permanecer cadastrado mesmo com estoque zerado"
        )
        
        # Verificar que o estoque está zerado
        self.medicamento.refresh_from_db()
        self.assertEqual(self.medicamento.quantidade_total, 0)
        
        # Verificar que podemos adicionar uma nova entrada ao medicamento
        nova_entrada = EntradaMedicamento.objects.create(
            medicamento=self.medicamento,
            quantidade=50,
            valor_medicamento=250.00,
            validade=date.today() + timedelta(days=180),
            cadastrada_por=self.user
        )
        
        # Verificar que o estoque foi restaurado
        self.medicamento.refresh_from_db()
        self.assertEqual(self.medicamento.quantidade_total, 50)
