"""
Middleware para gerenciar a fazenda ativa do usuário na sessão
"""
from django.shortcuts import redirect
from django.urls import reverse
from .models import Fazenda, PerfilUsuario


class FazendaMiddleware:
    """
    Middleware que garante que o usuário tenha uma fazenda ativa selecionada
    e filtra os dados apenas da fazenda ativa.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que não precisam de fazenda ativa
        self.urls_publicas = [
            '/login/',
            '/logout/',
            '/cadastro/',
            '/admin/',
            '/selecionar-fazenda/',
            '/static/',
            '/criar-fazenda/',
        ]
    
    def __call__(self, request):
        # Ignora URLs públicas e usuários não autenticados
        if not request.user.is_authenticated or any(request.path.startswith(url) for url in self.urls_publicas):
            response = self.get_response(request)
            return response
        
        # Verifica se o usuário tem perfil
        if not hasattr(request.user, 'perfil'):
            PerfilUsuario.objects.create(user=request.user)
        
        perfil = request.user.perfil
        
        # Obtém a fazenda ativa da sessão
        fazenda_id = request.session.get('fazenda_ativa_id')
        
        if fazenda_id:
            try:
                fazenda_ativa = Fazenda.objects.get(id=fazenda_id)
                # Verifica se o usuário ainda tem acesso a essa fazenda
                if not (fazenda_ativa in perfil.fazendas.all() or fazenda_ativa.dono == request.user):
                    # Remove fazenda inválida da sessão
                    del request.session['fazenda_ativa_id']
                    fazenda_ativa = None
                else:
                    request.fazenda_ativa = fazenda_ativa
            except Fazenda.DoesNotExist:
                del request.session['fazenda_ativa_id']
                fazenda_ativa = None
        else:
            fazenda_ativa = None
        
        # Se não tem fazenda ativa, tenta definir uma
        if not fazenda_ativa:
            # Busca fazendas do usuário (próprias ou com acesso)
            fazendas_usuario = perfil.fazendas.filter(ativa=True) | Fazenda.objects.filter(dono=request.user, ativa=True)
            fazendas_usuario = fazendas_usuario.distinct()
            
            if fazendas_usuario.exists():
                # Se tem apenas uma fazenda, seleciona automaticamente
                if fazendas_usuario.count() == 1:
                    fazenda_ativa = fazendas_usuario.first()
                    request.session['fazenda_ativa_id'] = fazenda_ativa.id
                    request.fazenda_ativa = fazenda_ativa
                else:
                    # Tem múltiplas fazendas, redireciona para seleção
                    if request.path != reverse('selecionar_fazenda'):
                        return redirect('selecionar_fazenda')
            else:
                # Não tem nenhuma fazenda, redireciona para criar
                if request.path not in [reverse('criar_fazenda'), reverse('logout')]:
                    return redirect('criar_fazenda')
        
        response = self.get_response(request)
        return response
