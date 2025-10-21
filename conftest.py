"""
Factories para criação de dados de teste usando Factory Boy
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User, Group
from faker import Faker
from datetime import date, timedelta
from decimal import Decimal

fake = Faker('pt_BR')


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            obj.set_password(extracted)
        else:
            obj.set_password('testpass123')


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
    
    name = factory.Sequence(lambda n: f'group{n}')


class ParceirosFactory(DjangoModelFactory):
    class Meta:
        model = 'perfis.Parceiros'
        django_get_or_create = ('nome',)
    
    nome = factory.Faker('company', locale='pt_BR')
    telefone = factory.Faker('phone_number', locale='pt_BR')
    email = factory.Faker('email', locale='pt_BR')
    if_adicionais = factory.Faker('text', max_nb_chars=200, locale='pt_BR')


class FazendaFactory(DjangoModelFactory):
    class Meta:
        model = 'perfis.Fazenda'
        django_get_or_create = ('nome',)
    
    nome = factory.Sequence(lambda n: f'Fazenda {n}')
    cidade = factory.Faker('city', locale='pt_BR')
    descricao = factory.Faker('text', max_nb_chars=200, locale='pt_BR')

    @factory.post_generation
    def usuarios(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for user in extracted:
                self.usuarios.add(user)


class CategoriaFactory(DjangoModelFactory):
    class Meta:
        model = 'movimentacao.Categoria'
        django_get_or_create = ('nome', 'tipo')
    
    nome = factory.Sequence(lambda n: f'Categoria {n}')
    tipo = factory.Iterator(['receita', 'despesa'])


class MovimentacaoFactory(DjangoModelFactory):
    class Meta:
        model = 'movimentacao.Movimentacao'
    
    tipo = factory.Iterator(['receita', 'despesa'])
    parceiros = factory.SubFactory(ParceirosFactory)
    categoria = factory.SubFactory(CategoriaFactory)
    valor_total = factory.LazyFunction(lambda: Decimal(fake.random_number(digits=5, fix_len=False)))
    parcelas = factory.LazyFunction(lambda: fake.random_int(min=1, max=12))
    imposto_renda = factory.Faker('boolean')
    descricao = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
    data = factory.LazyFunction(lambda: fake.date_between(start_date='-1y', end_date='today'))
    fazenda = factory.SubFactory(FazendaFactory)
    cadastrada_por = factory.SubFactory(UserFactory)


class ParcelaFactory(DjangoModelFactory):
    class Meta:
        model = 'movimentacao.Parcela'
    
    movimentacao = factory.SubFactory(MovimentacaoFactory)
    ordem_parcela = factory.Sequence(lambda n: n + 1)
    valor_parcela = factory.LazyFunction(lambda: Decimal(fake.random_number(digits=4, fix_len=False)))
    data_vencimento = factory.LazyFunction(lambda: fake.date_between(start_date='today', end_date='+1y'))
    valor_pago = Decimal('0.00')
    status_pagamento = 'Pendente'
    data_quitacao = None


class MedicamentoFactory(DjangoModelFactory):
    class Meta:
        model = 'medicamento.Medicamento'
        django_get_or_create = ('nome', 'fazenda')
    
    nome = factory.Sequence(lambda n: f'Medicamento {n}')
    fazenda = factory.SubFactory(FazendaFactory)


class EntradaMedicamentoFactory(DjangoModelFactory):
    class Meta:
        model = 'medicamento.EntradaMedicamento'
    
    medicamento = factory.SubFactory(MedicamentoFactory)
    valor_medicamento = factory.LazyFunction(lambda: Decimal(fake.random_number(digits=4, fix_len=False)))
    quantidade = factory.LazyFunction(lambda: fake.random_int(min=1, max=1000))
    validade = factory.LazyFunction(lambda: fake.date_between(start_date='today', end_date='+2y'))
    cadastrada_por = factory.SubFactory(UserFactory)
    observacao = factory.Faker('text', max_nb_chars=200, locale='pt_BR')
