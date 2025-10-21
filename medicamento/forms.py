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
        fields = ['nome', 'fazenda']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-field-full',
                'placeholder': 'Ex: Ivermectina, Dipirona, etc.',
                'required': True,
            }),
            'fazenda': forms.Select(attrs={
                'class': 'form-control form-field-full',
                'required': True,
            }),
        }
        
        labels = {
            'nome': 'Nome do Medicamento',
            'fazenda': 'Fazenda',
        }
        
        help_texts = {
            'nome': 'Digite o nome completo do medicamento',
            'fazenda': 'Selecione a fazenda onde o medicamento será armazenado',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona classes personalizadas
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'autocomplete': 'off'
            })


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
            'cadastrada_por',
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
            'valor_medicamento': forms.NumberInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'R$ 0,00',
                'step': '0.01',
                'min': '0',
                'required': True,
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
            'cadastrada_por': forms.Select(attrs={
                'class': 'form-control form-field-full',
                'readonly': True,
                'disabled': True,
            }),
        }
        
        labels = {
            'medicamento': 'Medicamento',
            'quantidade': 'Quantidade (unidades)',
            'valor_medicamento': 'Valor Total (R$)',
            'validade': 'Data de Validade',
            'observacao': 'Observações / Lote',
            'cadastrada_por': 'Cadastrado por',
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
        super().__init__(*args, **kwargs)
        
        # Define o usuário logado como valor inicial
        if user:
            self.fields['cadastrada_por'].initial = user
            self.fields['cadastrada_por'].widget.attrs['disabled'] = True
        
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
    
    def clean_cadastrada_por(self):
        # Garante que o campo cadastrada_por mantenha o valor original
        if self.instance and self.instance.pk:
            return self.instance.cadastrada_por
        return self.cleaned_data.get('cadastrada_por')
