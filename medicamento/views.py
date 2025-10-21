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
from medicamento.forms import MedicamentoForm, EntradaMedicamentoForm
from perfis.models import Fazenda


############ Create Medicamento ############
class MedicamentoCreateView(LoginRequiredMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "medicamento/cadastro_medicamento.html"
    success_url = reverse_lazy("medicamento_estoque")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Medicamentos",
            "titulo": "Cadastro de Medicamentos",
            "subtitulo": "Registre novos medicamentos no estoque da fazenda.",
        })
        return context


############ Create EntradaMedicamento ############
class EntradaMedicamentoCreateView(LoginRequiredMixin, CreateView):
    model = EntradaMedicamento
    form_class = EntradaMedicamentoForm
    template_name = "medicamento/cadastro_entrada.html"
    success_url = reverse_lazy("medicamento_estoque")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Define o usuário logado como cadastrado_por
        form.instance.cadastrada_por = self.request.user
        messages.success(
            self.request,
            f'Entrada de {form.instance.quantidade} unidades de '
            f'{form.instance.medicamento.nome} cadastrada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Entrada de Medicamentos",
            "titulo": "Nova Entrada de Medicamento",
            "subtitulo": "Registre a entrada de medicamentos no estoque da fazenda com informações de quantidade, valor e validade.",
        })
        return context



############ Update EntradaMedicamento ############
class EntradaMedicamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = EntradaMedicamento
    form_class = EntradaMedicamentoForm
    template_name = "medicamento/cadastro_entrada.html"
    success_url = reverse_lazy("medicamento_estoque")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Entrada de {form.instance.medicamento.nome} atualizada com sucesso!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Atualização de Entrada de Medicamentos",
            "titulo": "Atualizar Entrada de Medicamento",
            "subtitulo": "Atualize os dados da entrada de medicamentos no estoque da fazenda.",
        })
        return context


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

