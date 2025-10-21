from django import forms
from .models import Parceiros, Fazenda


class ParceirosForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro de parceiros/fornecedores.
    Layout otimizado com campos lado a lado.
    """
    
    class Meta:
        model = Parceiros
        fields = ['nome', 'telefone', 'email', 'if_adicionais']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-field-full',
                'placeholder': 'Ex: Agropecuária Silva, Veterinária Central, etc.',
                'required': True,
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': '(00) 00000-0000',
                'maxlength': '15',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'contato@empresa.com',
            }),
            'if_adicionais': forms.Textarea(attrs={
                'class': 'form-control form-field-full',
                'rows': 4,
                'placeholder': 'Informações adicionais sobre o parceiro: endereço, especialidades, condições de pagamento, etc.',
            }),
        }
        
        labels = {
            'nome': 'Nome do Parceiro/Fornecedor',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'if_adicionais': 'Informações Adicionais',
        }
        
        help_texts = {
            'nome': 'Nome completo da empresa ou pessoa física',
            'telefone': 'Telefone de contato principal',
            'email': 'E-mail para contato e envio de documentos',
            'if_adicionais': 'Endereço, CNPJ/CPF, condições comerciais, etc.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona classes personalizadas
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'autocomplete': 'off'
            })
    
    def clean_nome(self):
        """
        Valida se o nome não está vazio
        """
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 3:
                raise forms.ValidationError(
                    'O nome deve ter pelo menos 3 caracteres.'
                )
        return nome
    
    def clean_email(self):
        """
        Valida formato do email
        """
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
        return email


class FazendaForm(forms.ModelForm):
    """
    Formulário personalizado para cadastro de fazendas.
    Layout otimizado com campos lado a lado.
    """
    
    class Meta:
        model = Fazenda
        fields = ['nome', 'cidade', 'usuarios', 'descricao']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: Fazenda Santa Rita, Sítio Boa Vista, etc.',
                'required': True,
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: São Paulo - SP',
            }),
            'usuarios': forms.SelectMultiple(attrs={
                'class': 'form-control form-field-full',
                'size': '4',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-field-full',
                'rows': 4,
                'placeholder': 'Informações sobre a fazenda: área, tipo de produção, localização detalhada, etc.',
            }),
        }
        
        labels = {
            'nome': 'Nome da Fazenda',
            'cidade': 'Cidade/Estado',
            'usuarios': 'Usuários Responsáveis',
            'descricao': 'Descrição',
        }
        
        help_texts = {
            'nome': 'Nome ou identificação da propriedade rural',
            'cidade': 'Cidade e estado onde está localizada',
            'usuarios': 'Selecione um ou mais usuários responsáveis pela fazenda (segure Ctrl para múltipla seleção)',
            'descricao': 'Informações adicionais: tamanho da área, tipo de criação, etc.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona classes personalizadas
        for field_name, field in self.fields.items():
            if field_name != 'usuarios':
                field.widget.attrs.update({
                    'autocomplete': 'off'
                })
    
    def clean_nome(self):
        """
        Valida se o nome não está vazio
        """
        nome = self.cleaned_data.get('nome')
        if nome:
            nome = nome.strip()
            if len(nome) < 3:
                raise forms.ValidationError(
                    'O nome deve ter pelo menos 3 caracteres.'
                )
        return nome
