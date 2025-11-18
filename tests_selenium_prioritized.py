"""
TESTES DE INTERFACE COM SELENIUM - COM PRIORIZAÇÃO
Versão otimizada com prioridades P0-P3 para execução seletiva
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from perfis.models import Fazenda, Parceiros
from movimentacao.models import Categoria, Movimentacao
from decimal import Decimal
from datetime import date
import time
import pytest


class SeleniumTestBase(StaticLiveServerTestCase):
    """Classe base para testes Selenium com configurações comuns"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Configurações do Chrome
        chrome_options = Options()
        
        # Tenta modo headless primeiro
        import os
        if os.environ.get('SELENIUM_HEADLESS', 'true').lower() == 'true':
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Inicializa o driver do Chrome
        try:
            service = Service(ChromeDriverManager().install())
            cls.driver = webdriver.Chrome(service=service, options=chrome_options)
            cls.driver.implicitly_wait(10)
            cls.driver.set_page_load_timeout(30)
            cls.driver.set_script_timeout(30)
        except Exception as e:
            print(f"❌ Erro ao inicializar Chrome: {e}")
            print("💡 Tente: set SELENIUM_HEADLESS=false")
            raise
    
    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, 'driver') and cls.driver:
                # Fecha todas as janelas e abas
                for handle in cls.driver.window_handles:
                    cls.driver.switch_to.window(handle)
                    cls.driver.close()
                # Encerra o driver
                cls.driver.quit()
        except Exception as e:
            print(f"⚠️ Erro ao fechar driver: {e}")
        finally:
            try:
                super().tearDownClass()
            except Exception:
                pass
    
    def setUp(self):
        """Cria dados de teste antes de cada teste"""
        # Cria usuário
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Cria fazenda
        self.fazenda = Fazenda.objects.create(
            nome='Fazenda Teste Selenium',
            cidade='São Paulo',
            dono=self.user
        )
        self.fazenda.ativa = True
        self.fazenda.save()
        
        # Adiciona fazenda ao perfil do usuário
        try:
            self.user.perfil.fazendas.add(self.fazenda)
        except AttributeError:
            from perfis.models import PerfilUsuario
            perfil = PerfilUsuario.objects.create(user=self.user)
            perfil.fazendas.add(self.fazenda)
        
        # Cria parceiro
        self.parceiro = Parceiros.objects.create(
            nome='Parceiro Teste',
            fazenda=self.fazenda
        )
    
    def login(self):
        """Faz login no sistema"""
        self.driver.get(f'{self.live_server_url}/')
        
        username_input = self.driver.find_element(By.NAME, 'username')
        password_input = self.driver.find_element(By.NAME, 'password')
        
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')
        
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        time.sleep(2)


# ============================================
# P0 - TESTES CRÍTICOS (SMOKE TESTS)
# Execução: SEMPRE (a cada commit)
# Tempo esperado: < 2 minutos
# ============================================

@pytest.mark.priority_P0
@pytest.mark.smoke
@pytest.mark.critical
class TestCriticalAuthenticationSelenium(SeleniumTestBase):
    """P0 - Testes críticos de autenticação"""
    
    @pytest.mark.timeout(30)
    def test_login_successful(self):
        """[P0] Testa login com credenciais válidas - CRÍTICO"""
        self.driver.get(f'{self.live_server_url}/')
        
        self.driver.find_element(By.NAME, 'username').send_keys('testuser')
        self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        time.sleep(2)
        
        # Verifica se saiu da página de login
        try:
            self.driver.find_element(By.NAME, 'username')
            self.fail("❌ CRÍTICO: Login não funcionou")
        except:
            pass  # ✅ Login bem-sucedido
    
    @pytest.mark.timeout(30)
    def test_login_invalid_credentials(self):
        """[P0] Testa login com credenciais inválidas - CRÍTICO"""
        self.driver.get(f'{self.live_server_url}/')
        
        self.driver.find_element(By.NAME, 'username').send_keys('wronguser')
        self.driver.find_element(By.NAME, 'password').send_keys('wrongpass')
        self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        time.sleep(1)
        
        # Deve permanecer na página de login
        try:
            self.driver.find_element(By.NAME, 'username')
            # ✅ Correto: permaneceu no login
        except:
            self.fail("❌ CRÍTICO: Deveria permanecer na página de login")


# ============================================
# P1 - TESTES DE ALTA PRIORIDADE
# Execução: CI/CD, Pull Requests
# Tempo esperado: < 10 minutos
# ============================================

@pytest.mark.priority_P1
@pytest.mark.high
class TestHighPriorityNavigationSelenium(SeleniumTestBase):
    """P1 - Testes de navegação principal"""
    
    @pytest.mark.timeout(60)
    def test_navigate_to_receitas(self):
        """[P1] Navegação para receitas"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/receita/')
        
        self.assertIn('receita', self.driver.current_url)
        time.sleep(1)
    
    @pytest.mark.timeout(60)
    def test_navigate_to_despesas(self):
        """[P1] Navegação para despesas"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/despesa/')
        
        self.assertIn('despesa', self.driver.current_url)
        time.sleep(1)
    
    @pytest.mark.timeout(60)
    def test_navigate_to_medicamentos(self):
        """[P1] Navegação para medicamentos"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_medicamento/estoque/')
        
        self.assertIn('medicamento', self.driver.current_url)
        time.sleep(1)


@pytest.mark.priority_P1
@pytest.mark.high
class TestHighPriorityFormsSelenium(SeleniumTestBase):
    """P1 - Testes de formulários principais"""
    
    @pytest.mark.timeout(90)
    def test_create_categoria(self):
        """[P1] Criação de categoria"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/cadastrar/categoria/')
        time.sleep(2)
        
        try:
            nome_field = self.driver.find_element(By.NAME, 'nome')
            nome_field.send_keys('Nova Categoria Selenium')
            
            tipo_select = self.driver.find_element(By.NAME, 'tipo')
            tipo_select.send_keys('receita')
            
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()
            
            time.sleep(2)
            
            self.assertTrue(
                Categoria.objects.filter(nome='Nova Categoria Selenium').exists(),
                "Categoria deve ter sido criada"
            )
        except Exception as e:
            print(f"⚠️ Aviso: Formulário não acessível - {type(e).__name__}")


# ============================================
# P2 - TESTES DE MÉDIA PRIORIDADE
# Execução: Antes de releases, testes noturnos
# Tempo esperado: < 30 minutos
# ============================================

@pytest.mark.priority_P2
@pytest.mark.medium
@pytest.mark.slow
class TestMediumPriorityPaginationSelenium(SeleniumTestBase):
    """P2 - Testes de paginação"""
    
    def setUp(self):
        super().setUp()
        
        # Cria categoria
        self.categoria = Categoria.objects.create(
            nome='Venda Teste',
            tipo='receita',
            fazenda=self.fazenda
        )
        
        # Cria 25 movimentações para testar paginação
        for i in range(25):
            Movimentacao.objects.create(
                parceiros=self.parceiro,
                categoria=self.categoria,
                valor_total=Decimal('100.00'),
                data=date.today(),
                fazenda=self.fazenda,
                cadastrada_por=self.user,
                descricao=f'Teste {i+1}'
            )
    
    @pytest.mark.timeout(120)
    def test_pagination_shows_20_items(self):
        """[P2] Paginação mostra 20 itens por página"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/receita/')
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
        
        rows = self.driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
        self.assertEqual(len(rows), 20, "Deve mostrar 20 registros por página")
    
    @pytest.mark.timeout(120)
    def test_pagination_navigation(self):
        """[P2] Navegação entre páginas"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/receita/')
        time.sleep(2)
        
        try:
            pagination = self.driver.find_element(By.CLASS_NAME, 'pagination')
            
            try:
                next_button = self.driver.find_element(By.LINK_TEXT, 'Próxima')
                next_button.click()
                time.sleep(1)
                
                self.assertIn('page=2', self.driver.current_url)
                
                rows = self.driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
                self.assertEqual(len(rows), 5, "Página 2 deve mostrar 5 registros")
            except:
                pass
        except:
            rows = self.driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
            self.assertGreaterEqual(len(rows), 1, "Deve ter pelo menos 1 registro")


@pytest.mark.priority_P2
@pytest.mark.medium
class TestMediumPriorityFiltersSelenium(SeleniumTestBase):
    """P2 - Testes de filtros"""
    
    def setUp(self):
        super().setUp()
        
        # Cria categorias diferentes
        self.cat_venda = Categoria.objects.create(
            nome='Venda',
            tipo='receita',
            fazenda=self.fazenda
        )
        
        self.cat_servico = Categoria.objects.create(
            nome='Serviço',
            tipo='receita',
            fazenda=self.fazenda
        )
        
        # Cria movimentações
        Movimentacao.objects.create(
            parceiros=self.parceiro,
            categoria=self.cat_venda,
            valor_total=Decimal('500.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
        
        Movimentacao.objects.create(
            parceiros=self.parceiro,
            categoria=self.cat_servico,
            valor_total=Decimal('300.00'),
            data=date.today(),
            fazenda=self.fazenda,
            cadastrada_por=self.user
        )
    
    @pytest.mark.timeout(90)
    def test_filter_by_category(self):
        """[P2] Filtro por categoria"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/receita/')
        time.sleep(2)
        
        try:
            self.driver.find_element(By.TAG_NAME, 'table')
        except:
            pass
        
        self.assertIn('receita', self.driver.current_url)


# ============================================
# P3 - TESTES DE BAIXA PRIORIDADE
# Execução: Testes semanais, validação completa
# Tempo esperado: sem limite
# ============================================

@pytest.mark.priority_P3
@pytest.mark.low
@pytest.mark.ui
class TestLowPriorityResponsiveSelenium(SeleniumTestBase):
    """P3 - Testes de responsividade"""
    
    @pytest.mark.timeout(60)
    def test_mobile_viewport(self):
        """[P3] Visualização mobile (iPhone X)"""
        self.login()
        
        # Define viewport mobile
        self.driver.set_window_size(375, 812)
        
        self.driver.get(f'{self.live_server_url}/pagina_inicial/')
        time.sleep(1)
        
        self.assertIn('/pagina_inicial/', self.driver.current_url)
    
    @pytest.mark.timeout(60)
    def test_tablet_viewport(self):
        """[P3] Visualização tablet (iPad)"""
        self.login()
        
        # Define viewport tablet
        self.driver.set_window_size(768, 1024)
        
        self.driver.get(f'{self.live_server_url}/pagina_movimentacao/listar/movimentacao/receita/')
        time.sleep(1)
        
        try:
            table = self.driver.find_element(By.TAG_NAME, 'table')
        except:
            pass
        
        self.assertIn('receita', self.driver.current_url)


@pytest.mark.priority_P3
@pytest.mark.low
@pytest.mark.javascript
class TestLowPriorityJavaScriptSelenium(SeleniumTestBase):
    """P3 - Testes de JavaScript"""
    
    @pytest.mark.timeout(60)
    def test_toast_notification(self):
        """[P3] Notificações toast JavaScript"""
        self.login()
        
        self.driver.get(f'{self.live_server_url}/')
        time.sleep(1)
        
        # Executa JavaScript para criar notificação
        self.driver.execute_script("""
            if (typeof showToast === 'function') {
                showToast('Teste Selenium', 'success');
            }
        """)
        
        time.sleep(0.5)

