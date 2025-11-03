from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.


class Fazenda(models.Model):
    """
    Modelo principal para isolamento multi-tenant.
    Cada fazenda possui seus próprios dados isolados.
    """
    nome = models.CharField(max_length=100, verbose_name='Nome da Fazenda')
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cidade')
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name='Estado (UF)')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    dono = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='fazendas_proprietario',
        verbose_name='Proprietário',
        help_text='Produtor responsável pela fazenda'
    )
    ativa = models.BooleanField(default=True, verbose_name='Fazenda Ativa')
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    
    def __str__(self):
        return f"{self.nome}" + (f" - {self.cidade}" if self.cidade else "")

    class Meta:
        verbose_name = 'Fazenda'
        verbose_name_plural = 'Fazendas'
        ordering = ['nome']


class PerfilUsuario(models.Model):
    """
    Perfil estendido do usuário com informações adicionais
    e controle de acesso a fazendas.
    """
    TIPO_USUARIO_CHOICES = [
        ('produtor', 'Produtor'),
        ('funcionario', 'Funcionário'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuário'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='funcionario',
        verbose_name='Tipo de Usuário'
    )
    fazendas = models.ManyToManyField(
        Fazenda,
        related_name='usuarios',
        verbose_name='Fazendas com Acesso',
        blank=True,
        help_text='Fazendas que este usuário pode acessar'
    )
    telefone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Telefone')
    cpf = models.CharField(max_length=14, blank=True, null=True, unique=True, verbose_name='CPF')
    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data de Nascimento')
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_tipo_display()})"
    
    def eh_produtor(self):
        """Verifica se o usuário é um produtor"""
        return self.tipo == 'produtor'
    
    def eh_funcionario(self):
        """Verifica se o usuário é um funcionário"""
        return self.tipo == 'funcionario'
    
    def pode_acessar_fazenda(self, fazenda):
        """Verifica se o usuário tem acesso a uma fazenda específica"""
        return fazenda in self.fazendas.all() or fazenda.dono == self.user

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        ordering = ['user__first_name', 'user__username']


@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente um perfil quando um usuário é criado
    """
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def salvar_perfil_usuario(sender, instance, **kwargs):
    """
    Signal para salvar o perfil quando o usuário é salvo
    """
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


class Parceiros(models.Model):
    """
    Empresas parceiras da fazenda (fornecedores, compradores, etc.)
    """
    nome = models.CharField(max_length=100, verbose_name='Nome da Empresa Parceira')
    telefone = models.CharField(max_length=15, blank=True, null=True, verbose_name='Telefone')
    if_adicionais = models.TextField(blank=True, null=True, verbose_name='Informações Adicionais')
    email = models.EmailField(max_length=254, blank=True, null=True, verbose_name='E-mail')
    fazenda = models.ForeignKey(
        Fazenda,
        on_delete=models.CASCADE,
        verbose_name='Fazenda',
        related_name='parceiros'
    )
    
    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = 'Parceiro'
        verbose_name_plural = 'Parceiros'
        ordering = ['nome']
        unique_together = [['nome', 'fazenda']]  # Mesmo parceiro pode existir em fazendas diferentes