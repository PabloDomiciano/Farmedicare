from django import forms
from django.contrib.auth.models import User
from .models import Parceiros, Fazenda, PerfilUsuario


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
        fields = ['nome', 'cidade', 'estado', 'descricao']
        
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: Fazenda Santa Rita, Sítio Boa Vista, etc.',
                'required': True,
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: Ribeirão Preto',
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control form-field-half',
                'placeholder': 'Ex: SP',
                'maxlength': '2',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control form-field-full',
                'rows': 4,
                'placeholder': 'Informações sobre a fazenda: área, tipo de produção, localização detalhada, etc.',
            }),
        }
        
        labels = {
            'nome': 'Nome da Fazenda',
            'cidade': 'Cidade',
            'estado': 'Estado (UF)',
            'descricao': 'Descrição',
        }
        
        help_texts = {
            'nome': 'Nome ou identificação da propriedade rural',
            'cidade': 'Cidade onde está localizada a fazenda',
            'estado': 'Sigla do estado (ex: SP, MG, RJ)',
            'descricao': 'Informações adicionais: tamanho da área, tipo de criação, etc.',
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
    
    def clean_estado(self):
        """
        Valida e formata o estado (UF)
        """
        estado = self.cleaned_data.get('estado')
        if estado:
            estado = estado.strip().upper()
            if len(estado) != 2:
                raise forms.ValidationError(
                    'Digite a sigla do estado com 2 letras (ex: SP, MG, RJ).'
                )
        return estado


class AdicionarFuncionarioExistenteForm(forms.Form):
    """
    Formulário para adicionar um funcionário já existente a uma fazenda.
    """
    funcionario = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.none(),
        label='Selecione o Funcionário',
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text='Escolha um funcionário já cadastrado no sistema.'
    )
    
    def __init__(self, *args, fazenda=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if fazenda:
            # Busca funcionários do mesmo dono que ainda não estão nesta fazenda
            funcionarios_do_dono = PerfilUsuario.objects.filter(
                tipo='funcionario',
                fazendas__dono=fazenda.dono
            ).exclude(
                fazendas=fazenda
            ).distinct().select_related('user')
            
            self.fields['funcionario'].queryset = funcionarios_do_dono
            
            # Customiza a exibição no select
            self.fields['funcionario'].label_from_instance = lambda obj: f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email}) - {obj.fazendas.count()} fazenda(s)"


class FuncionarioForm(forms.Form):
    """
    Formulário para cadastrar um novo funcionário vinculado a uma fazenda específica.
    Cria o usuário Django e o perfil automaticamente.
    """
    
    # Dados do usuário
    username = forms.CharField(
        label='Nome de Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: joao.silva',
            'autocomplete': 'off',
        }),
        help_text='Nome único para login no sistema (sem espaços ou caracteres especiais).'
    )
    
    first_name = forms.CharField(
        label='Primeiro Nome',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: João',
            'autocomplete': 'off',
        }),
        help_text='Primeiro nome do funcionário.'
    )
    
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Silva',
            'autocomplete': 'off',
        }),
        help_text='Sobrenome do funcionário.'
    )
    
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'funcionario@email.com',
            'autocomplete': 'off',
        }),
        help_text='E-mail para contato e recuperação de senha.'
    )
    
    # Dados do perfil
    telefone = forms.CharField(
        label='Telefone',
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(00) 00000-0000',
            'autocomplete': 'off',
        }),
        help_text='Telefone de contato (opcional).'
    )
    
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'autocomplete': 'off',
        }),
        help_text='CPF do funcionário (opcional).'
    )
    
    # Senha
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
        help_text='Senha com no mínimo 8 caracteres.'
    )
    
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
        help_text='Digite a mesma senha novamente.'
    )
    
    def clean_username(self):
        """Valida se o username já não existe"""
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip().lower()
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError(
                    'Este nome de usuário já está em uso. Escolha outro.'
                )
        return username
    
    def clean_email(self):
        """Valida se o email já não existe"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    'Este e-mail já está cadastrado no sistema.'
                )
        return email
    
    def clean_password1(self):
        """Valida a força da senha"""
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise forms.ValidationError(
                'A senha deve ter no mínimo 8 caracteres.'
            )
        return password
    
    def clean(self):
        """Valida se as senhas são iguais"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                'As senhas não coincidem. Digite a mesma senha nos dois campos.'
            )
        
        return cleaned_data
    
    def save(self, fazenda):
        """
        Cria o usuário, o perfil e vincula à fazenda especificada.
        Retorna o usuário criado.
        """
        # Cria o usuário
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        
        # Atualiza o perfil (criado automaticamente pelo signal)
        perfil = user.perfil
        perfil.tipo = 'funcionario'
        perfil.telefone = self.cleaned_data.get('telefone', '')
        perfil.cpf = self.cleaned_data.get('cpf', '')
        perfil.save()
        
        # Vincula o funcionário à fazenda
        perfil.fazendas.add(fazenda)
        
        return user
