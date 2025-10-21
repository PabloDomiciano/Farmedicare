from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from datetime import date, timedelta

from medicamento.models import EntradaMedicamento, Medicamento
from medicamento.notificacoes import gerar_notificacoes_medicamentos
from perfis.models import Fazenda


############ Create Medicamento ############
class MedicamentoCreateView(LoginRequiredMixin, CreateView):
    model = Medicamento
    fields = ["nome", "fazenda"]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("pagina_index")
    extra_context = {
        "title": "Cadastro de Medicamentos",
        "titulo": "Cadastro de Medicamentos",
        "subtitulo": "Registre novos medicamentos no estoque da fazenda.",
    }


############ Create EntradaMedicamento ############
class EntradaMedicamentoCreateView(LoginRequiredMixin, CreateView):
    model = EntradaMedicamento
    fields = ["medicamento", "valor_medicamento", "quantidade", "validade", "cadastrada_por", "observacao"]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("medicamento_estoque")
    extra_context = {
        "title": "Cadastro de Entrada de Medicamentos",
        "titulo": "Cadastro de Entrada de Medicamentos",
        "subtitulo": "Registre a entrada de medicamentos no estoque da fazenda.",
    }



############ Update EntradaMedicamento ############
class EntradaMedicamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = EntradaMedicamento
    fields = ["medicamento", "valor_medicamento", "quantidade", "validade", "cadastrada_por", "observacao"]
    template_name = "formularios/formulario_modelo.html"
    success_url = reverse_lazy("medicamento_estoque")
    extra_context = {
        "title": "Atualização de Entrada de Medicamentos",
        "titulo": "Atualização de Entrada de Medicamentos",
        "subtitulo": "Atualize os dados da entrada de medicamentos no estoque da fazenda.",
    }


############ Delete EntradaMedicamento ############
class EntradaMedicamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = EntradaMedicamento
    template_name = 'formularios/formulario_excluir.html'
    success_url = reverse_lazy("medicamento_estoque")
    extra_context = {
        "titulo": "Confirmação de Exclusão",
    }


############ List EntradaMedicamento (Legado) ############
class EntradaMedicamentoListView(LoginRequiredMixin, ListView):
    model = EntradaMedicamento
    template_name = "medicamento_estoque.html"
    extra_context = {
        "title": "Lista de Entradas de Medicamentos",
        "titulo": "Entradas de Medicamentos",
        "registros": "Nenhuma entrada de medicamento encontrada.",
        "subtitulo": "Visualize todas as entradas de medicamentos registradas.",
        "btn_cadastrar":  "Nova Entrada"
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcula os totais
        total_quantidade = 0
        total_valor = 0
        
        for entrada in context['object_list']:
            total_quantidade += entrada.quantidade
            total_valor += entrada.valor_medicamento
        
        context['total_quantidade'] = total_quantidade
        context['total_valor'] = total_valor
        
        return context


############ List Medicamentos com Controle de Validade (NOVA) ############
class MedicamentoEstoqueListView(LoginRequiredMixin, ListView):
    model = Medicamento
    template_name = "medicamento_estoque_novo.html"
    context_object_name = "medicamentos"
    
    def get_queryset(self):
        return Medicamento.objects.all().prefetch_related('entradamedicamento_set')
    
    def get_context_data(self, **kwargs):
        from datetime import date, timedelta
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        
        # Preparar dados dos medicamentos com informações de validade
        medicamentos_data = []
        total_medicamentos = 0
        total_quantidade = 0
        vencidos = 0
        proximo_vencer = 0  # 30 dias
        atencao = 0  # 60 dias
        
        for medicamento in context['medicamentos']:
            entradas = medicamento.entradamedicamento_set.all().order_by('validade')
            
            if not entradas:
                continue
                
            # Pegar a entrada com validade mais próxima
            proxima_entrada = entradas.first()
            dias_para_vencer = (proxima_entrada.validade - hoje).days
            
            # Determinar status
            if dias_para_vencer < 0:
                status = 'vencido'
                vencidos += 1
            elif dias_para_vencer <= 30:
                status = 'critico'
                proximo_vencer += 1
            elif dias_para_vencer <= 60:
                status = 'atencao'
                atencao += 1
            else:
                status = 'ok'
            
            # Calcular totais deste medicamento
            quantidade_total = sum(e.quantidade for e in entradas)
            valor_total = sum(e.valor_medicamento for e in entradas)
            
            medicamentos_data.append({
                'id': medicamento.id,
                'nome': medicamento.nome,
                'fazenda': medicamento.fazenda,
                'quantidade_total': quantidade_total,
                'valor_total': valor_total,
                'proxima_validade': proxima_entrada.validade,
                'dias_para_vencer': dias_para_vencer,
                'dias_vencido_abs': abs(dias_para_vencer) if dias_para_vencer < 0 else 0,
                'status': status,
                'lote': proxima_entrada.observacao if proxima_entrada.observacao else '-',
                'total_entradas': entradas.count()
            })
            
            total_medicamentos += 1
            total_quantidade += quantidade_total
        
        # Ordenar por dias para vencer (mais urgente primeiro)
        medicamentos_data.sort(key=lambda x: x['dias_para_vencer'])
        
        context['medicamentos_data'] = medicamentos_data
        context['total_medicamentos'] = total_medicamentos
        context['total_quantidade'] = total_quantidade
        context['vencidos'] = vencidos
        context['proximo_vencer'] = proximo_vencer
        context['atencao'] = atencao
        context['ok'] = total_medicamentos - vencidos - proximo_vencer - atencao
        context['today'] = hoje
        context['title'] = "Controle de Validade de Medicamentos"
        context['titulo'] = "Controle de Validade de Medicamentos"
        context['btn_cadastrar'] = "Nova Entrada"
        context['registros'] = "Nenhum medicamento encontrado."
        
        return context


############ Página de Notificações ############
class NotificacoesListView(LoginRequiredMixin, TemplateView):
    template_name = "notificacoes.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dados_notificacoes = gerar_notificacoes_medicamentos()
        
        context['notificacoes'] = dados_notificacoes['notificacoes']
        context['total'] = dados_notificacoes['total']
        context['vencidos'] = dados_notificacoes['vencidos']
        context['proximos_vencer'] = dados_notificacoes['proximos_vencer']
        context['hoje'] = dados_notificacoes['hoje']
        context['title'] = "Notificações - Medicamentos"
        context['titulo'] = "Notificações de Medicamentos"
        context['btn_voltar'] = "Voltar ao Estoque"
        
        return context


############ API JSON de Notificações ############
class NotificacoesAPIView(LoginRequiredMixin, View):
    """
    API endpoint que retorna notificações em formato JSON
    para o popup de notificações
    """
    def get(self, request, *args, **kwargs):
        dados_notificacoes = gerar_notificacoes_medicamentos()
        
        # Serializar as notificações para JSON
        notificacoes_json = []
        for notif in dados_notificacoes['notificacoes']:
            notificacoes_json.append({
                'tipo': notif['tipo'],
                'urgencia': notif['urgencia'],
                'icone': notif['icone'],
                'cor': notif['cor'],
                'mensagem': notif['mensagem'],
                'medicamento': notif['medicamento'],
                'medicamento_id': notif['medicamento_id'],
                'quantidade': notif['quantidade'],
                'validade': notif['validade'].isoformat(),  # Converter data para ISO format
                'dias_para_vencer': notif['dias_para_vencer'],
                'dias_vencido_abs': notif['dias_vencido_abs'],
                'fazenda': notif['fazenda'],
                'lote': notif['lote'],
            })
        
        return JsonResponse({
            'notificacoes': notificacoes_json,
            'total': dados_notificacoes['total'],
            'vencidos': dados_notificacoes['vencidos'],
            'proximos_vencer': dados_notificacoes['proximos_vencer'],
        })


class CriarMedicamentoTesteView(LoginRequiredMixin, View):
    """
    View para criar medicamentos de teste com diferentes datas de validade
    para testar o sistema de notificações.
    """
    
    def get(self, request):
        # Pegar a primeira fazenda do usuário ou criar uma
        fazenda = Fazenda.objects.filter(nome__icontains='fazenda').first()
        if not fazenda:
            fazenda = Fazenda.objects.first()
        
        if not fazenda:
            messages.error(request, 'Nenhuma fazenda encontrada! Crie uma fazenda primeiro.')
            return redirect('medicamento_estoque')
        
        usuario = request.user
        hoje = date.today()
        
        # Lista de medicamentos de teste com diferentes validades
        medicamentos_teste = [
            {
                'nome': 'Ivermectina TESTE - VENCIDO',
                'dias': -10,  # Vencido há 10 dias
                'quantidade': 5,
                'valor': 150.00
            },
            {
                'nome': 'Vermífugo TESTE - VENCIDO',
                'dias': -25,  # Vencido há 25 dias
                'quantidade': 3,
                'valor': 80.00
            },
            {
                'nome': 'Antibiótico TESTE - CRÍTICO',
                'dias': 5,  # Vence em 5 dias
                'quantidade': 8,
                'valor': 200.00
            },
            {
                'nome': 'Vitamina TESTE - CRÍTICO',
                'dias': 15,  # Vence em 15 dias
                'quantidade': 10,
                'valor': 120.00
            },
            {
                'nome': 'Vacina TESTE - CRÍTICO',
                'dias': 28,  # Vence em 28 dias
                'quantidade': 12,
                'valor': 300.00
            },
            {
                'nome': 'Anti-inflamatório TESTE - ATENÇÃO',
                'dias': 45,  # Vence em 45 dias
                'quantidade': 6,
                'valor': 180.00
            },
            {
                'nome': 'Analgésico TESTE - OK',
                'dias': 90,  # Vence em 90 dias
                'quantidade': 15,
                'valor': 250.00
            },
        ]
        
        criados = 0
        for med_data in medicamentos_teste:
            # Criar ou pegar o medicamento
            medicamento, created = Medicamento.objects.get_or_create(
                nome=med_data['nome'],
                fazenda=fazenda
            )
            
            # Calcular data de validade
            data_validade = hoje + timedelta(days=med_data['dias'])
            
            # Criar entrada de medicamento
            EntradaMedicamento.objects.create(
                medicamento=medicamento,
                valor_medicamento=med_data['valor'],
                quantidade=med_data['quantidade'],
                validade=data_validade,
                cadastrada_por=usuario,
                observacao=f"Medicamento de TESTE criado automaticamente para testar notificações (Vence em {med_data['dias']} dias)"
            )
            
            criados += 1
        
        messages.success(request, f'✅ {criados} medicamentos de TESTE criados com sucesso! Agora você pode testar as notificações.')
        return redirect('medicamento_estoque')
