from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from datetime import date, timedelta
import json

from medicamento.models import EntradaMedicamento, Medicamento, SaidaMedicamento
from medicamento.notificacoes import gerar_notificacoes_medicamentos
from medicamento.forms import MedicamentoForm, EntradaMedicamentoForm
from medicamento.filters import EntradaMedicamentoFilter
from perfis.models import Fazenda


############ Create Medicamento ############
class MedicamentoCreateView(LoginRequiredMixin, CreateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "medicamento/cadastro_medicamento.html"
    success_url = reverse_lazy("listar_medicamentos")
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Medicamento "{form.instance.nome}" cadastrado com sucesso!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao cadastrar medicamento. Verifique os dados.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Cadastro de Medicamentos",
            "titulo": "Cadastro de Medicamentos",
            "subtitulo": "Registre novos medicamentos no estoque da fazenda.",
        })
        return context


############ Update Medicamento ############
class MedicamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Medicamento
    form_class = MedicamentoForm
    template_name = "medicamento/cadastro_medicamento.html"
    success_url = reverse_lazy("listar_medicamentos")
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'✅ Medicamento "{form.instance.nome}" atualizado com sucesso!'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Atualização de Medicamento",
            "titulo": "Atualizar Medicamento",
            "subtitulo": "Atualize os dados do medicamento.",
        })
        return context


############ Delete Medicamento ############
class MedicamentoDeleteView(LoginRequiredMixin, DeleteView):
    model = Medicamento
    template_name = "formularios/formulario_excluir.html"
    success_url = reverse_lazy("listar_medicamentos")
    
    def delete(self, request, *args, **kwargs):
        medicamento = self.get_object()
        medicamento_nome = medicamento.nome
        fazenda_nome = medicamento.fazenda.nome
        messages.success(
            self.request,
            f'🗑️ Medicamento "{medicamento_nome}" excluído com sucesso! Fazenda: {fazenda_nome}'
        )
        return super().delete(request, *args, **kwargs)
    
    extra_context = {
        "title": "Exclusão de Medicamento",
        "titulo_excluir": "Exclusão de Medicamento",
    }


############ List Medicamentos ############
class MedicamentoListView(LoginRequiredMixin, ListView):
    model = Medicamento
    template_name = "medicamento/lista_medicamentos.html"
    context_object_name = "medicamentos"
    login_url = reverse_lazy("login")

    def get_queryset(self):
        return (
            Medicamento.objects.all()
            .select_related("fazenda")
            .only("id", "nome", "fazenda__nome")
            .order_by("nome")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista de Medicamentos"
        context["titulo"] = "Medicamentos"
        
        # Calcular total de medicamentos (usar count() ao invés de len())
        context["total_medicamentos"] = self.get_queryset().count()
        
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
        messages.success(
            self.request,
            f'✅ Entrada de medicamento "{form.instance.medicamento.nome}" registrada! Quantidade: {form.instance.quantidade}'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Erro ao registrar entrada de medicamento. Verifique os dados.'
        )
        return super().form_invalid(form)
    
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
    
    def delete(self, request, *args, **kwargs):
        entrada = self.get_object()
        medicamento_nome = entrada.medicamento.nome
        quantidade = entrada.quantidade
        quantidade_disponivel = entrada.quantidade_disponivel
        data_validade = entrada.validade.strftime('%d/%m/%Y')
        fazenda_nome = entrada.medicamento.fazenda.nome
        
        messages.success(
            self.request,
            f'🗑️ Entrada de medicamento excluída com sucesso! {medicamento_nome} - '
            f'Qtd: {quantidade_disponivel}/{quantidade} - Validade: {data_validade} - Fazenda: {fazenda_nome}'
        )
        return super().delete(request, *args, **kwargs)


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
    model = EntradaMedicamento
    template_name = "medicamento_estoque_novo.html"
    context_object_name = "entradas"
    paginate_by = 20
    filterset_class = EntradaMedicamentoFilter
    
    def get_queryset(self):
        queryset = (
            EntradaMedicamento.objects.all()
            .select_related('medicamento', 'medicamento__fazenda')
            .only(
                'id', 'quantidade', 'quantidade_disponivel', 'validade', 
                'valor_medicamento', 'observacao', 'data_cadastro',
                'medicamento__id', 'medicamento__nome', 
                'medicamento__fazenda__id', 'medicamento__fazenda__nome'
            )
            .order_by('validade')
        )
        
        # Pesquisa por texto (busca em todos os registros)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(medicamento__nome__icontains=search_query) |
                Q(medicamento__fazenda__nome__icontains=search_query) |
                Q(observacao__icontains=search_query)
            )
        
        # Aplicar filtros
        self.filterset = EntradaMedicamentoFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
    
    def get_context_data(self, **kwargs):
        from datetime import date, timedelta
        context = super().get_context_data(**kwargs)
        hoje = date.today()
        
        # Adicionar parâmetro de pesquisa ao contexto
        context['search_query'] = self.request.GET.get('search', '')
        
        # Preparar dados das entradas com informações de validade
        entradas_data = []
        total_medicamentos = 0
        total_quantidade = 0
        vencidos = 0
        proximo_vencer = 0  # 30 dias
        atencao = 0  # 60 dias
        
        # Usar queryset filtrado para os cálculos
        for entrada in self.filterset.qs:
            medicamento = entrada.medicamento
            
            # Usar quantidade_disponivel (descontando saídas)
            quantidade_disponivel = entrada.quantidade_disponivel
            
            # Ignorar entradas com quantidade zero (já utilizadas completamente)
            if quantidade_disponivel <= 0:
                continue
            
            dias_para_vencer = (entrada.validade - hoje).days
            
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
            
            entradas_data.append({
                'id': medicamento.id,
                'entrada_id': entrada.id,
                'nome': medicamento.nome,
                'fazenda': medicamento.fazenda,
                'quantidade_total': quantidade_disponivel,
                'valor_total': entrada.valor_medicamento,
                'proxima_validade': entrada.validade,
                'dias_para_vencer': dias_para_vencer,
                'dias_vencido_abs': abs(dias_para_vencer) if dias_para_vencer < 0 else 0,
                'status': status,
                'lote': entrada.observacao if entrada.observacao else f'Entrada #{entrada.id}',
                'data_cadastro': entrada.data_cadastro
            })
            
            total_medicamentos += 1
            total_quantidade += quantidade_disponivel
        
        # Ordenar por dias para vencer (mais urgente primeiro)
        entradas_data.sort(key=lambda x: x['dias_para_vencer'])
        
        context['medicamentos_data'] = entradas_data
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
        context['registros'] = "Nenhuma entrada de medicamento encontrada."
        context['filter'] = self.filterset
        
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


############ API de Saída de Medicamento ############
@method_decorator(csrf_exempt, name='dispatch')
class SaidaMedicamentoAPIView(LoginRequiredMixin, View):
    """
    API endpoint para registrar saída de medicamentos
    Implementa lógica FIFO (First In, First Out) - saída das entradas mais antigas primeiro
    """
    def post(self, request, *args, **kwargs):
        from django.db import transaction
        
        try:
            print(f"DEBUG - Request body: {request.body}")
            
            # Parsear o JSON do corpo da requisição
            data = json.loads(request.body)
            
            print(f"DEBUG - Dados recebidos: {data}")
            
            medicamento_id = data.get('medicamento_id')
            quantidade_solicitada = data.get('quantidade')
            motivo = data.get('motivo', '')
            
            print(f"DEBUG - Medicamento ID: {medicamento_id}, Quantidade: {quantidade_solicitada}")
            
            # Validações
            if not medicamento_id or not quantidade_solicitada:
                return JsonResponse({
                    'success': False,
                    'error': 'Medicamento e quantidade são obrigatórios.'
                }, status=400)
            
            try:
                quantidade_solicitada = int(quantidade_solicitada)
                if quantidade_solicitada <= 0:
                    raise ValueError
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Quantidade deve ser um número positivo.'
                }, status=400)
            
            # Usar transaction para garantir atomicidade e select_for_update para evitar race condition
            with transaction.atomic():
                # Buscar o medicamento
                medicamento = get_object_or_404(Medicamento, id=medicamento_id)
                print(f"DEBUG - Medicamento encontrado: {medicamento.nome}")
                
                # Buscar entradas com quantidade disponível, ordenadas por validade (FIFO)
                # select_for_update() trava as linhas para evitar concorrência
                entradas_disponiveis = EntradaMedicamento.objects.select_for_update().filter(
                    medicamento=medicamento,
                    quantidade_disponivel__gt=0
                ).order_by('validade')
                
                if not entradas_disponiveis.exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Não há estoque disponível para este medicamento.'
                    }, status=400)
                
                # Verificar se há estoque suficiente total
                estoque_total = sum(e.quantidade_disponivel for e in entradas_disponiveis)
                print(f"DEBUG - Estoque total disponível: {estoque_total}")
                
                if quantidade_solicitada > estoque_total:
                    return JsonResponse({
                        'success': False,
                        'error': f'Estoque insuficiente. Disponível: {estoque_total} unidades.'
                    }, status=400)
                
                # Implementar lógica FIFO - retirar das entradas mais antigas primeiro
                quantidade_restante = quantidade_solicitada
                entradas_processadas = []
                
                for entrada in entradas_disponiveis:
                    if quantidade_restante <= 0:
                        break
                    
                    # Quantidade a retirar desta entrada
                    quantidade_desta_entrada = min(quantidade_restante, entrada.quantidade_disponivel)
                    
                    # Atualizar quantidade disponível da entrada
                    entrada.quantidade_disponivel -= quantidade_desta_entrada
                    entrada.save(update_fields=['quantidade_disponivel'])
                    
                    # Registrar a saída
                    saida = SaidaMedicamento.objects.create(
                        medicamento=medicamento,
                        entrada=entrada,
                        quantidade=quantidade_desta_entrada,
                        motivo=motivo,
                        registrada_por=request.user
                    )
                    
                    entradas_processadas.append({
                        'entrada_id': entrada.id,
                        'quantidade': quantidade_desta_entrada,
                        'saida_id': saida.id
                    })
                    
                    print(f"DEBUG - Saída criada: {quantidade_desta_entrada} da entrada #{entrada.id}")
                    
                    # Reduzir quantidade restante
                    quantidade_restante -= quantidade_desta_entrada
                    
                    # Se a entrada zerou, ela não será mais exibida (filtro na view)
                    if entrada.quantidade_disponivel == 0:
                        print(f"DEBUG - Entrada #{entrada.id} zerada (não será mais exibida)")
                
                # Calcular novo estoque total
                novo_estoque = medicamento.quantidade_total
                print(f"DEBUG - Novo estoque total: {novo_estoque}")
                
                # Se o estoque zerou completamente, deletar o medicamento
                if novo_estoque <= 0:
                    nome_medicamento = medicamento.nome
                    medicamento.delete()  # Isso também deleta as entradas e saídas por CASCADE
                    print(f"DEBUG - Medicamento {nome_medicamento} removido (estoque zerado)")
                    mensagem = f'Saída de {quantidade_solicitada} unidades registrada! O medicamento {nome_medicamento} foi removido do estoque (quantidade zerada).'
                else:
                    mensagem = f'Saída de {quantidade_solicitada} unidades registrada com sucesso!'
                
                return JsonResponse({
                    'success': True,
                    'message': mensagem,
                    'novo_estoque': novo_estoque,
                    'estoque_zerado': novo_estoque <= 0,
                    'entradas_processadas': entradas_processadas
                })
            
        except json.JSONDecodeError:
            print("DEBUG - Erro ao decodificar JSON")
            return JsonResponse({
                'success': False,
                'error': 'Dados JSON inválidos.'
            }, status=400)
        except Exception as e:
            print(f"DEBUG - Erro: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Erro ao processar saída: {str(e)}'
            }, status=500)

