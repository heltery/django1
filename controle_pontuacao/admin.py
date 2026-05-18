from django.contrib import admin
from django.contrib.auth.models import User

from .models import OcorrenciaVinculada, TipoOcorrencia, UsoPontuacao, saldo_usuario


@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pontuacao', 'ativo', 'atualizado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')


@admin.register(OcorrenciaVinculada)
class OcorrenciaVinculadaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'pontuacao_aplicada', 'data_ocorrencia', 'criado_por')
    list_filter = ('tipo', 'data_ocorrencia')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'tipo__nome')
    autocomplete_fields = ('usuario', 'tipo')
    readonly_fields = ('criado_por', 'criado_em')

    def save_model(self, request, obj, form, change):
        if not obj.criado_por_id:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(UsoPontuacao)
class UsoPontuacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'descricao', 'pontos', 'data_uso', 'registrado_por')
    list_filter = ('data_uso',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'descricao')
    autocomplete_fields = ('usuario',)
    readonly_fields = ('registrado_por', 'criado_em')

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


def saldo_atual(obj):
    return saldo_usuario(obj)


saldo_atual.short_description = 'saldo de pontos'

try:
    user_admin = admin.site._registry[User]
    user_admin.list_display = tuple(user_admin.list_display) + ('saldo_atual',)
    user_admin.saldo_atual = saldo_atual
except KeyError:
    pass
