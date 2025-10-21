from django import forms
from .models import Movimentacao, Categoria
from perfis.models import Parceiros, Fazenda


class MovimentacaoForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro de movimentações.
    Layout otimizado com campos lado a lado para melhor usabilidade.
    """
    
    class Meta:
        model = Movimentacao
        fields = [
            'tipo',
            'categoria',
            'parceiros',
            'fazenda',
            'valor_total',
            'parcelas',
            'imposto_renda',
            'data',
            'descricao',
            'cadastrada_por',
        ]
        
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control form-field-half',
                'required': True,
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control form-field-half',
                'required': True,
            }),
            'parceiros': forms.Select(attrs={
                'class': 'form-control form-field-half',
                'required': True,
            }),
            'fazenda': forms.Select(attrs={
                'class': 'form-control form-field-half',
                'required': True,
            }),
            'valor_total': forms.NumberInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'R$ 0,00',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'parcelas': forms.NumberInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Número de parcelas',
                'min': '1',
                'value': '1',
                'required': True,
            }),
            'imposto_renda': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control form-field-half',
                'type': 'date',
                'required': True,
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-field-full',
                'rows': 3,
                'placeholder': 'Descreva os detalhes da movimentação...',
            }),
            'cadastrada_por': forms.Select(attrs={
                'class': 'form-control form-field-full',
                'readonly': True,
                'disabled': True,
            }),
        }
        
        labels = {
            'tipo': 'Tipo de Movimentação',
            'categoria': 'Categoria',
            'parceiros': 'Parceiro/Fornecedor',
            'fazenda': 'Fazenda',
            'valor_total': 'Valor Total (R$)',
            'parcelas': 'Número de Parcelas',
            'imposto_renda': 'Declarar no Imposto de Renda?',
            'data': 'Data da Movimentação',
            'descricao': 'Descrição/Observações',
            'cadastrada_por': 'Cadastrado por',
        }
        
        help_texts = {
            'tipo': 'Selecione se é uma receita ou despesa',
            'valor_total': 'Valor total da movimentação',
            'parcelas': 'Quantidade de parcelas para pagamento/recebimento',
            'imposto_renda': 'Marque se esta movimentação deve ser declarada no IR',
            'descricao': 'Informações adicionais sobre a movimentação',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Define o usuário logado como valor inicial
        if user:
            self.fields['cadastrada_por'].initial = user
            self.fields['cadastrada_por'].widget.attrs['disabled'] = True
        
        # Adiciona classes personalizadas para estilização
        for field_name, field in self.fields.items():
            if field_name != 'imposto_renda':
                field.widget.attrs.update({
                    'autocomplete': 'off'
                })
    
    def clean_cadastrada_por(self):
        # Garante que o campo cadastrada_por mantenha o valor original
        if self.instance and self.instance.pk:
            return self.instance.cadastrada_por
        return self.cleaned_data.get('cadastrada_por')
