from django import forms
from .models import Movimentacao, Categoria
from perfis.models import Parceiros, Fazenda


class CategoriaForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro e edição de categorias.
    Categorias são utilizadas para classificar receitas e despesas.
    """
    
    class Meta:
        model = Categoria
        fields = ['nome', 'tipo']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Venda de Produtos, Salários, Manutenção...',
                'required': True,
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
        }
        
        labels = {
            'nome': 'Nome da Categoria',
            'tipo': 'Tipo de Categoria',
        }
        
        help_texts = {
            'nome': 'Digite um nome descritivo para identificar esta categoria',
            'tipo': 'Selecione se esta categoria será usada para receitas ou despesas',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona autocomplete off para todos os campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'autocomplete': 'off'
            })


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
            # 'cadastrada_por' - definido automaticamente pela view
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
        tipo_fixo = kwargs.pop('tipo_fixo', None)  # Novo parâmetro para tipo fixo
        super().__init__(*args, **kwargs)
        
        # Se tipo_fixo foi passado, configura o campo como disabled e com valor fixo
        if tipo_fixo:
            self.fields['tipo'].initial = tipo_fixo
            self.fields['tipo'].widget.attrs.update({
                'disabled': True,
                'class': 'form-control form-field-half campo-bloqueado',
            })
            # Armazena o tipo fixo para usar no clean
            self.tipo_fixo = tipo_fixo
            
            # Filtra as categorias pelo tipo
            self.fields['categoria'].queryset = Categoria.objects.filter(tipo=tipo_fixo).order_by('nome')
        else:
            self.tipo_fixo = None
        
        # Adiciona classes personalizadas para estilização
        for field_name, field in self.fields.items():
            if field_name != 'imposto_renda':
                field.widget.attrs.update({
                    'autocomplete': 'off'
                })
    
    def clean_tipo(self):
        """
        Garante que o tipo fixo seja mantido mesmo com o campo disabled
        """
        if self.tipo_fixo:
            return self.tipo_fixo
        return self.cleaned_data.get('tipo')
    
    # Removido clean_cadastrada_por - campo não está mais no formulário
