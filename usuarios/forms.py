from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class UsuarioCadastroForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}
        ),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]


    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já existe.")
        return username


class UsuarioUpdateForm(forms.ModelForm):
    """
    Formulário personalizado para atualização de dados de usuários.
    Permite editar informações básicas sem alterar a senha.
    """
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome de usuário único',
                'required': True,
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: João',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Silva',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@exemplo.com',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        
        labels = {
            'username': 'Nome de Usuário',
            'first_name': 'Primeiro Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'is_active': 'Usuário Ativo',
        }
        
        help_texts = {
            'username': 'Nome único para login no sistema',
            'first_name': 'Primeiro nome do usuário',
            'last_name': 'Sobrenome do usuário',
            'email': 'Endereço de e-mail para contato',
            'is_active': 'Desmarque para desativar o acesso do usuário sem excluí-lo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona autocomplete off para todos os campos
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs.update({
                    'autocomplete': 'off'
                })
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Verifica se o username já existe (exceto para o próprio usuário)
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verifica se o email já existe (exceto para o próprio usuário)
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email
