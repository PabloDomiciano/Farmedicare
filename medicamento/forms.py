from django import forms
from .models import Medicamento, EntradaMedicamento
from perfis.models import Fazenda
from datetime import date, timedelta


class MedicamentoForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro de medicamentos.
    Layout otimizado e simples.
    """
    
    class Meta:
        model = Medicamento
        fields = ['nome']  # Fazenda será auto-atribuída pela view
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-field-full',
                'placeholder': 'Ex: Ivermectina, Dipirona, etc.',
                'required': True,
            }),
        }
        
        labels = {
            'nome': 'Nome do Medicamento',
        }
        
        help_texts = {
            'nome': 'Digite o nome completo do medicamento',
        }
    
    def __init__(self, *args, **kwargs):
        self.fazenda_ativa = kwargs.pop('fazenda_ativa', None)
        super().__init__(*args, **kwargs)
        
        # Adiciona classes personalizadas
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'autocomplete': 'off'
            })
    
    def clean_nome(self):
        """Valida se o medicamento já existe na fazenda"""
        nome = self.cleaned_data.get('nome')
        
        if nome and self.fazenda_ativa:
            # Verifica se já existe um medicamento com esse nome na fazenda
            # Exclui o próprio objeto se estiver editando
            queryset = Medicamento.objects.filter(
                nome__iexact=nome,  # Case-insensitive
                fazenda=self.fazenda_ativa
            )
            
            # Se estiver editando, exclui o próprio registro
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    f'O medicamento "{nome}" já está cadastrado nesta fazenda. '
                    'Por favor, use outro nome ou adicione uma entrada para o medicamento existente.'
                )
        
        return nome


class EntradaMedicamentoForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro de entrada de medicamentos.
    Layout otimizado com campos lado a lado.
    """
    
    class Meta:
        model = EntradaMedicamento
        fields = [
            'medicamento',
            'quantidade',
            'valor_medicamento',
            'validade',
            'observacao',
            # 'cadastrada_por' - definido automaticamente pela view
        ]
        
        widgets = {
            'medicamento': forms.Select(attrs={
                'class': 'form-control form-field-half',
                'required': True,
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: 100',
                'min': '1',
                'required': True,
            }),
            'valor_medicamento': forms.TextInput(attrs={
                'class': 'form-control form-field-half money-input',
                'placeholder': '0,00',
                'required': True,
                'inputmode': 'decimal',
            }),
            'validade': forms.DateInput(attrs={
                'class': 'form-control form-field-half',
                'type': 'date',
                'required': True,
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control form-field-full',
                'rows': 3,
                'placeholder': 'Informações adicionais: lote, fornecedor, observações sobre o medicamento...',
            }),
        }
        
        labels = {
            'medicamento': 'Medicamento',
            'quantidade': 'Quantidade (unidades)',
            'valor_medicamento': 'Valor Total (R$)',
            'validade': 'Data de Validade',
            'observacao': 'Observações / Lote',
        }
        
        help_texts = {
            'medicamento': 'Selecione o medicamento ou cadastre um novo',
            'quantidade': 'Quantidade de unidades que está sendo adicionada ao estoque',
            'valor_medicamento': 'Valor total pago por esta quantidade',
            'validade': 'Data de vencimento do medicamento',
            'observacao': 'Informações como número do lote, fornecedor, etc.',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        fazenda_ativa = kwargs.pop('fazenda_ativa', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar medicamentos apenas da fazenda ativa
        if fazenda_ativa:
            self.fields['medicamento'].queryset = Medicamento.objects.filter(
                fazenda=fazenda_ativa
            ).order_by('nome')
        else:
            # Se não houver fazenda ativa, não mostra nenhum medicamento
            self.fields['medicamento'].queryset = Medicamento.objects.none()
        
        # Define data mínima para validade (hoje)
        hoje = date.today()
        self.fields['validade'].widget.attrs['min'] = hoje.isoformat()
        
        # Adiciona classes personalizadas
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'autocomplete': 'off'
            })
    
    def clean_validade(self):
        """
        Valida se a data de validade não está no passado
        """
        validade = self.cleaned_data.get('validade')
        if validade and validade < date.today():
            raise forms.ValidationError(
                'A data de validade não pode estar no passado. '
                'Verifique a data informada.'
            )
        return validade
    
    def clean_quantidade(self):
        """
        Valida se a quantidade é positiva
        """
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade and quantidade <= 0:
            raise forms.ValidationError(
                'A quantidade deve ser maior que zero.'
            )
        return quantidade
    
    def clean_valor_medicamento(self):
        """
        Valida se o valor é positivo
        """
        valor = self.cleaned_data.get('valor_medicamento')
        if valor and valor < 0:
            raise forms.ValidationError(
                'O valor não pode ser negativo.'
            )
        return valor
    
    # Removido clean_cadastrada_por - campo não está mais no formulário
