from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Fazenda, Parceiros, PerfilUsuario

# Register your models here.


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    filter_horizontal = ('fazendas',)


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)


# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Fazenda)
class FazendaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'dono', 'ativa', 'data_criacao')
    list_filter = ('ativa', 'estado', 'data_criacao')
    search_fields = ('nome', 'cidade', 'dono__username', 'dono__first_name', 'dono__last_name')
    date_hierarchy = 'data_criacao'
    readonly_fields = ('data_criacao',)


@admin.register(Parceiros)
class ParceirosAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fazenda', 'telefone', 'email')
    list_filter = ('fazenda',)
    search_fields = ('nome', 'email', 'telefone')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'telefone', 'cpf')
    list_filter = ('tipo',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cpf', 'telefone')
    filter_horizontal = ('fazendas',)
