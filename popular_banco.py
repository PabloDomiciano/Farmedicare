"""
Script para popular o banco de dados com dados realistas de 6 meses de operação
"""
import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmedicare.settings')
django.setup()

from django.contrib.auth.models import User, Group
from perfis.models import Fazenda, Parceiros
from medicamento.models import Medicamento, EntradaMedicamento
from movimentacao.models import Categoria, Movimentacao, Parcela

def limpar_banco():
    """Limpa todos os dados do banco"""
    print("🗑️  Limpando banco de dados...")
    
    # Deletar na ordem correta para respeitar foreign keys
    Parcela.objects.all().delete()
    Movimentacao.objects.all().delete()
    EntradaMedicamento.objects.all().delete()
    Medicamento.objects.all().delete()
    Categoria.objects.all().delete()
    Parceiros.objects.all().delete()
    Fazenda.objects.all().delete()
    User.objects.all().delete()
    Group.objects.all().delete()
    
    print("✅ Banco limpo!")

def criar_usuarios():
    """Cria usuários do sistema"""
    print("\n👥 Criando usuários...")
    
    # Criar grupos
    grupo_admin, _ = Group.objects.get_or_create(name='Administrador')
    grupo_func, _ = Group.objects.get_or_create(name='Funcionario')
    
    # Criar admin
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@farmedicare.com',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema'
    )
    admin.groups.add(grupo_admin)
    
    # Criar funcionários
    funcionarios = [
        ('joao.silva', 'João', 'Silva', 'joao@farmedicare.com'),
        ('maria.santos', 'Maria', 'Santos', 'maria@farmedicare.com'),
        ('pedro.oliveira', 'Pedro', 'Oliveira', 'pedro@farmedicare.com'),
    ]
    
    users_list = [admin]
    for username, first, last, email in funcionarios:
        user = User.objects.create_user(
            username=username,
            email=email,
            password='senha123',
            first_name=first,
            last_name=last
        )
        user.groups.add(grupo_func)
        users_list.append(user)
    
    print(f"✅ Criados {len(users_list)} usuários")
    return users_list

def criar_fazendas(users):
    """Cria fazendas"""
    print("\n🏡 Criando fazendas...")
    
    fazendas_data = [
        ('Fazenda Boa Vista', 'São Paulo', 'Fazenda especializada em gado leiteiro'),
        ('Fazenda Santa Maria', 'Minas Gerais', 'Produção de gado de corte'),
        ('Fazenda São José', 'Goiás', 'Agricultura e pecuária mista'),
    ]
    
    fazendas = []
    for nome, cidade, desc in fazendas_data:
        fazenda = Fazenda.objects.create(
            nome=nome,
            cidade=cidade,
            descricao=desc
        )
        # Adicionar usuários responsáveis
        fazenda.usuarios.add(*random.sample(users, k=random.randint(1, 2)))
        fazendas.append(fazenda)
    
    print(f"✅ Criadas {len(fazendas)} fazendas")
    return fazendas

def criar_parceiros():
    """Cria empresas parceiras"""
    print("\n🤝 Criando parceiros...")
    
    parceiros_data = [
        ('Cooperativa Agropecuária Central', '(11) 3456-7890', 'contato@cooperativa.com.br'),
        ('Veterinária São Francisco', '(11) 98765-4321', 'atendimento@vetsaofrancisco.com.br'),
        ('Distribuidora Agro Plus', '(11) 2345-6789', 'vendas@agroplus.com.br'),
        ('Frigorífico Bom Gado', '(11) 3456-1234', 'comercial@bomgado.com.br'),
        ('Laticínio Vale Verde', '(11) 98234-5678', 'compras@valeverde.com.br'),
        ('Farmácia Veterinária Animal Care', '(11) 3789-4561', 'vendas@animalcare.com.br'),
        ('Transportadora Rural Express', '(11) 97654-3210', 'logistica@ruralexpress.com.br'),
        ('Fornecedor de Ração Nutri Bov', '(11) 3234-5678', 'pedidos@nutribov.com.br'),
    ]
    
    parceiros = []
    for nome, tel, email in parceiros_data:
        parceiro = Parceiros.objects.create(
            nome=nome,
            telefone=tel,
            email=email,
            if_adicionais=f'Parceiro comercial há mais de 2 anos'
        )
        parceiros.append(parceiro)
    
    print(f"✅ Criados {len(parceiros)} parceiros")
    return parceiros

def criar_categorias():
    """Cria categorias de movimentação"""
    print("\n📊 Criando categorias...")
    
    categorias_receita = [
        'Venda de Leite',
        'Venda de Gado',
        'Venda de Bezerros',
        'Prestação de Serviços',
        'Venda de Esterco',
    ]
    
    categorias_despesa = [
        'Compra de Ração',
        'Medicamentos',
        'Manutenção de Equipamentos',
        'Salários',
        'Energia Elétrica',
        'Combustível',
        'Veterinário',
        'Impostos',
        'Transporte',
    ]
    
    categorias = []
    
    for nome in categorias_receita:
        cat = Categoria.objects.create(nome=nome, tipo='receita')
        categorias.append(cat)
    
    for nome in categorias_despesa:
        cat = Categoria.objects.create(nome=nome, tipo='despesa')
        categorias.append(cat)
    
    print(f"✅ Criadas {len(categorias)} categorias")
    return categorias

def criar_medicamentos(fazendas, users):
    """Cria medicamentos e suas entradas"""
    print("\n💊 Criando medicamentos e entradas...")
    
    medicamentos_data = [
        'Ivermectina 1%',
        'Complexo B',
        'Antibiótico Enrofloxacina',
        'Anti-inflamatório Meloxicam',
        'Vermífugo Albendazole',
        'Vacina Brucelose',
        'Vacina Febre Aftosa',
        'Carrapaticida',
        'Suplemento Mineral',
        'Vitamina ADE',
    ]
    
    total_entradas = 0
    
    for fazenda in fazendas:
        # Cada fazenda tem entre 6-8 medicamentos
        meds_fazenda = random.sample(medicamentos_data, k=random.randint(6, 8))
        
        for nome_med in meds_fazenda:
            med = Medicamento.objects.create(
                nome=nome_med,
                fazenda=fazenda
            )
            
            # Criar 3-6 entradas para cada medicamento nos últimos 6 meses
            num_entradas = random.randint(3, 6)
            
            for i in range(num_entradas):
                dias_atras = random.randint(0, 180)
                data_entrada = datetime.now() - timedelta(days=dias_atras)
                
                # Validade entre 1-3 anos
                validade = data_entrada.date() + timedelta(days=random.randint(365, 1095))
                
                entrada = EntradaMedicamento.objects.create(
                    medicamento=med,
                    valor_medicamento=Decimal(random.uniform(150, 2500)).quantize(Decimal('0.01')),
                    quantidade=random.randint(10, 200),
                    validade=validade,
                    cadastrada_por=random.choice(users),
                    observacao=f'Lote {random.randint(1000, 9999)}'
                )
                total_entradas += 1
    
    print(f"✅ Criados {Medicamento.objects.count()} medicamentos com {total_entradas} entradas")

def criar_movimentacoes(fazendas, parceiros, categorias, users):
    """Cria movimentações financeiras dos últimos 6 meses"""
    print("\n💰 Criando movimentações financeiras...")
    
    data_inicial = datetime.now() - timedelta(days=180)
    
    categorias_receita = [c for c in categorias if c.tipo == 'receita']
    categorias_despesa = [c for c in categorias if c.tipo == 'despesa']
    
    total_movimentacoes = 0
    
    for fazenda in fazendas:
        # Rastrear combinações já usadas: (tipo, parceiro_id, data, fazenda_id)
        combinacoes_usadas = set()
        
        # Criar movimentações para cada mês
        for mes in range(6):
            data_base = data_inicial + timedelta(days=30 * mes)
            
            # Receitas do mês (2-4 receitas)
            for _ in range(random.randint(2, 4)):
                tentativas = 0
                max_tentativas = 50
                sucesso = False
                
                while tentativas < max_tentativas and not sucesso:
                    tentativas += 1
                    
                    dias_offset = random.randint(0, 28)
                    data_mov = data_base + timedelta(days=dias_offset)
                    parceiro = random.choice(parceiros)
                    
                    # Criar combinação única
                    combinacao = ('receita', parceiro.id, data_mov.date(), fazenda.id)
                    
                    if combinacao in combinacoes_usadas:
                        continue  # Tentar outra combinação
                    
                    categoria = random.choice(categorias_receita)
                    parcelas = random.choice([1, 1, 1, 2, 3])  # Mais provável ser à vista
                    
                    try:
                        mov = Movimentacao.objects.create(
                            tipo='receita',
                            parceiros=parceiro,
                            categoria=categoria,
                            valor_total=Decimal(random.uniform(5000, 25000)).quantize(Decimal('0.01')),
                            parcelas=parcelas,
                            imposto_renda=random.choice([True, False]),
                            descricao=f'Receita de {categoria.nome.lower()} - {data_mov.strftime("%B/%Y")}',
                            data=data_mov.date(),
                            fazenda=fazenda,
                            cadastrada_por=random.choice(users)
                        )
                        
                        combinacoes_usadas.add(combinacao)
                        total_movimentacoes += 1
                        sucesso = True
                        
                        # Quitar algumas parcelas aleatoriamente
                        if random.random() > 0.3:  # 70% de chance de quitar
                            for parcela in mov.parcela_set.all():
                                if random.random() > 0.2:  # 80% de chance de quitar cada parcela
                                    parcela.valor_pago = parcela.valor_parcela
                                    parcela.status_pagamento = 'Pago'
                                    parcela.data_quitacao = parcela.data_vencimento + timedelta(days=random.randint(0, 5))
                                    parcela.save()
                        
                    except Exception:
                        continue  # Tentar novamente
            
            # Despesas do mês (4-7 despesas)
            for _ in range(random.randint(4, 7)):
                tentativas = 0
                max_tentativas = 50
                sucesso = False
                
                while tentativas < max_tentativas and not sucesso:
                    tentativas += 1
                    
                    dias_offset = random.randint(0, 28)
                    data_mov = data_base + timedelta(days=dias_offset)
                    parceiro = random.choice(parceiros)
                    
                    # Criar combinação única
                    combinacao = ('despesa', parceiro.id, data_mov.date(), fazenda.id)
                    
                    if combinacao in combinacoes_usadas:
                        continue  # Tentar outra combinação
                    
                    categoria = random.choice(categorias_despesa)
                    parcelas = random.choice([1, 1, 1, 2, 3, 4])
                    
                    try:
                        mov = Movimentacao.objects.create(
                            tipo='despesa',
                            parceiros=parceiro,
                            categoria=categoria,
                            valor_total=Decimal(random.uniform(800, 15000)).quantize(Decimal('0.01')),
                            parcelas=parcelas,
                            imposto_renda=False,
                            descricao=f'Despesa com {categoria.nome.lower()}',
                            data=data_mov.date(),
                            fazenda=fazenda,
                            cadastrada_por=random.choice(users)
                        )
                        
                        combinacoes_usadas.add(combinacao)
                        total_movimentacoes += 1
                        sucesso = True
                        
                        # Quitar algumas parcelas
                        if random.random() > 0.2:  # 80% de chance de quitar despesas
                            for parcela in mov.parcela_set.all():
                                if random.random() > 0.15:  # 85% de chance de quitar cada parcela
                                    parcela.valor_pago = parcela.valor_parcela
                                    parcela.status_pagamento = 'Pago'
                                    parcela.data_quitacao = parcela.data_vencimento + timedelta(days=random.randint(-2, 10))
                                    parcela.save()
                        
                    except Exception:
                        continue  # Tentar novamente
    
    print(f"✅ Criadas {total_movimentacoes} movimentações financeiras")
    print(f"   - Receitas: {Movimentacao.objects.filter(tipo='receita').count()}")
    print(f"   - Despesas: {Movimentacao.objects.filter(tipo='despesa').count()}")
    print(f"   - Total de parcelas: {Parcela.objects.count()}")
    print(f"   - Parcelas pagas: {Parcela.objects.filter(status_pagamento='Pago').count()}")

def main():
    """Função principal"""
    print("=" * 60)
    print("🌾 POPULANDO BANCO DE DADOS - FARMEDICARE")
    print("   Simulando 6 meses de operação")
    print("=" * 60)
    
    # Limpar banco
    limpar_banco()
    
    # Criar dados
    users = criar_usuarios()
    fazendas = criar_fazendas(users)
    parceiros = criar_parceiros()
    categorias = criar_categorias()
    criar_medicamentos(fazendas, users)
    criar_movimentacoes(fazendas, parceiros, categorias, users)
    
    print("\n" + "=" * 60)
    print("✅ BANCO POPULADO COM SUCESSO!")
    print("=" * 60)
    print("\n📊 RESUMO:")
    print(f"   👥 Usuários: {User.objects.count()}")
    print(f"   🏡 Fazendas: {Fazenda.objects.count()}")
    print(f"   🤝 Parceiros: {Parceiros.objects.count()}")
    print(f"   📊 Categorias: {Categoria.objects.count()}")
    print(f"   💊 Medicamentos: {Medicamento.objects.count()}")
    print(f"   📦 Entradas de Medicamentos: {EntradaMedicamento.objects.count()}")
    print(f"   💰 Movimentações: {Movimentacao.objects.count()}")
    print(f"   📄 Parcelas: {Parcela.objects.count()}")
    
    print("\n🔐 CREDENCIAIS DE ACESSO:")
    print("   Admin:")
    print("     Username: admin")
    print("     Password: admin123")
    print("\n   Funcionários:")
    print("     Username: joao.silva | maria.santos | pedro.oliveira")
    print("     Password: senha123")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
