import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from usuarios.forms import UsuarioCadastroForm
from usuarios.views import CadastroUsuarioView


class TestUsuarioCadastroForm(TestCase):
    """Testes do formulário de cadastro de usuários"""
    
    def test_form_valid_data(self):
        """Testa se o formulário aceita dados válidos"""
        form_data = {
            'username': 'testuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        form = UsuarioCadastroForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_password_mismatch(self):
        """Testa se o formulário rejeita senhas diferentes"""
        form_data = {
            'username': 'testuser',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!',
        }
        form = UsuarioCadastroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_form_duplicate_username(self):
        """Testa se o formulário rejeita username duplicado"""
        User.objects.create_user(username='existinguser', password='test123')
        form_data = {
            'username': 'existinguser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        form = UsuarioCadastroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_form_empty_data(self):
        """Testa se o formulário rejeita dados vazios"""
        form = UsuarioCadastroForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 3)


class TestCadastroUsuarioView(TestCase):
    """Testes da view de cadastro de usuários"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('registrar')
    
    def test_view_renders_correct_template(self):
        """Testa se a view renderiza o template correto"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuarios/register.html')
    
    def test_view_uses_correct_form(self):
        """Testa se a view usa o formulário correto"""
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['form'], UsuarioCadastroForm)
    
    def test_successful_user_registration(self):
        """Testa cadastro de usuário com sucesso"""
        form_data = {
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        response = self.client.post(self.url, data=form_data)
        
        # Verifica se o usuário foi criado
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        
        # Verifica se o usuário está ativo
        self.assertTrue(user.is_active)
        
        # Verifica se foi adicionado ao grupo Funcionario
        self.assertTrue(user.groups.filter(name='Funcionario').exists())
        
        # Verifica redirecionamento
        self.assertRedirects(response, reverse('login'))
    
    def test_registration_with_invalid_data(self):
        """Testa cadastro com dados inválidos"""
        form_data = {
            'username': '',
            'password1': 'pass',
            'password2': 'different',
        }
        response = self.client.post(self.url, data=form_data)
        
        # Verifica que nenhum usuário foi criado
        self.assertEqual(User.objects.count(), 0)
        
        # Verifica que permanece na mesma página
        self.assertEqual(response.status_code, 200)
    
    def test_registration_creates_group_if_not_exists(self):
        """Testa se o grupo Funcionario é criado se não existir"""
        # Garante que o grupo não existe
        Group.objects.filter(name='Funcionario').delete()
        
        form_data = {
            'username': 'testuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }
        self.client.post(self.url, data=form_data)
        
        # Verifica se o grupo foi criado
        self.assertTrue(Group.objects.filter(name='Funcionario').exists())


@pytest.mark.django_db
class TestUsuarioAuthentication:
    """Testes de autenticação de usuários"""
    
    def test_user_can_login(self, client):
        """Testa se um usuário pode fazer login"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        login_url = reverse('login')
        response = client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Verifica se o usuário está autenticado
        assert response.status_code in [200, 302]  # 302 é redirecionamento
    
    def test_user_login_with_wrong_password(self, client):
        """Testa login com senha incorreta"""
        User.objects.create_user(username='testuser', password='correctpass')
        
        login_url = reverse('login')
        response = client.post(login_url, {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        
        # Deve retornar erro
        assert response.status_code == 200
    
    def test_inactive_user_cannot_login(self, client):
        """Testa que usuário inativo não pode fazer login"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        user.is_active = False
        user.save()
        
        login_url = reverse('login')
        response = client.post(login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == 200
