"""
Context processors para disponibilizar informações globais nos templates
"""

def fazenda_ativa(request):
    """
    Adiciona a fazenda ativa e lista de fazendas do usuário no contexto
    """
    context = {
        'fazenda_ativa': None,
        'fazendas_usuario': [],
    }
    
    if request.user.is_authenticated and hasattr(request, 'fazenda_ativa'):
        context['fazenda_ativa'] = request.fazenda_ativa
        
        # Busca todas as fazendas do usuário
        if hasattr(request.user, 'perfil'):
            perfil = request.user.perfil
            from .models import Fazenda
            fazendas = perfil.fazendas.filter(ativa=True) | Fazenda.objects.filter(dono=request.user, ativa=True)
            context['fazendas_usuario'] = fazendas.distinct()
    
    return context
