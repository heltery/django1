from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User

from .models import OcorrenciaVinculada, TipoOcorrencia, UsoPontuacao, saldo_usuario


class AdministrativoAdminSite(admin.AdminSite):
    site_header = 'Administrativo BPRONE'
    site_title = 'Administrativo'
    index_title = 'Cadastros administrativos'
    site_url = '/sistema/'

    def has_permission(self, request):
        user = request.user
        return (
            user.is_active
            and user.is_authenticated
            and user.is_superuser
        )


administrativo_site = AdministrativoAdminSite(name='administrativo')


class UsuariosMultiplosMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['usuarios'].initial = [self.instance.usuario]

    def save(self, commit=True):
        obj = super().save(commit=False)
        usuarios = self.cleaned_data.get('usuarios')
        if usuarios:
            obj.usuario = usuarios[0]
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class OcorrenciaVinculadaForm(UsuariosMultiplosMixin, forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by('username'),
        label='Usuarios',
        widget=FilteredSelectMultiple('usuarios', is_stacked=False),
        help_text='Selecione um ou mais usuarios para criar a mesma ocorrencia para todos.',
    )

    class Meta:
        model = OcorrenciaVinculada
        exclude = ('usuario',)


class UsoPontuacaoForm(UsuariosMultiplosMixin, forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by('username'),
        label='Usuarios',
        widget=FilteredSelectMultiple('usuarios', is_stacked=False),
        help_text='Selecione um ou mais usuarios para registrar o mesmo uso de pontuacao para todos.',
    )

    class Meta:
        model = UsoPontuacao
        exclude = ('usuario',)


@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'pontuacao', 'ativo', 'atualizado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')


@admin.register(OcorrenciaVinculada)
class OcorrenciaVinculadaAdmin(admin.ModelAdmin):
    form = OcorrenciaVinculadaForm
    list_display = ('usuario', 'tipo', 'pontuacao_aplicada', 'data_ocorrencia', 'criado_por')
    fields = ('usuarios', 'tipo', 'pontuacao_aplicada', 'observacao', 'data_ocorrencia', 'criado_por', 'criado_em')
    list_filter = ('tipo', 'data_ocorrencia')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'tipo__nome')
    autocomplete_fields = ('tipo',)
    readonly_fields = ('criado_por', 'criado_em')

    class Media:
        css = {'all': ('controle_pontuacao/admin_multiselect.css',)}

    def save_model(self, request, obj, form, change):
        if not obj.criado_por_id:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

        usuarios = list(form.cleaned_data.get('usuarios') or [])
        for usuario in usuarios[1:]:
            OcorrenciaVinculada.objects.get_or_create(
                usuario=usuario,
                tipo=obj.tipo,
                pontuacao_aplicada=obj.pontuacao_aplicada,
                observacao=obj.observacao,
                data_ocorrencia=obj.data_ocorrencia,
                criado_por=obj.criado_por,
            )


@admin.register(UsoPontuacao)
class UsoPontuacaoAdmin(admin.ModelAdmin):
    form = UsoPontuacaoForm
    list_display = ('usuario', 'descricao', 'pontos', 'data_uso', 'registrado_por')
    fields = ('usuarios', 'descricao', 'pontos', 'data_uso', 'registrado_por', 'criado_em')
    list_filter = ('data_uso',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'descricao')
    readonly_fields = ('registrado_por', 'criado_em')

    class Media:
        css = {'all': ('controle_pontuacao/admin_multiselect.css',)}

    def save_model(self, request, obj, form, change):
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)

        usuarios = list(form.cleaned_data.get('usuarios') or [])
        for usuario in usuarios[1:]:
            UsoPontuacao.objects.get_or_create(
                usuario=usuario,
                descricao=obj.descricao,
                pontos=obj.pontos,
                data_uso=obj.data_uso,
                registrado_por=obj.registrado_por,
            )


def saldo_atual(obj):
    return saldo_usuario(obj)


saldo_atual.short_description = 'saldo de pontos'

try:
    user_admin = admin.site._registry[User]
    user_admin.list_display = tuple(user_admin.list_display) + ('saldo_atual',)
    user_admin.saldo_atual = saldo_atual
except KeyError:
    pass


class UsuarioAdministrativoAdmin(UserAdmin):
    list_display = tuple(UserAdmin.list_display) + ('saldo_atual',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(is_superuser=False)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if obj is None:
            return self.add_fieldsets
        return (
            (None, {'fields': ('username', 'password')}),
            ('Informacoes pessoais', {'fields': ('first_name', 'last_name', 'email')}),
            ('Permissoes', {'fields': ('is_active', 'groups')}),
            ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
        )

    def has_change_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.is_staff = False
            obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def saldo_atual(self, obj):
        return saldo_usuario(obj)

    saldo_atual.short_description = 'saldo de pontos'


administrativo_site.register(User, UsuarioAdministrativoAdmin)
administrativo_site.register(Group, GroupAdmin)
administrativo_site.register(TipoOcorrencia, TipoOcorrenciaAdmin)
administrativo_site.register(OcorrenciaVinculada, OcorrenciaVinculadaAdmin)
administrativo_site.register(UsoPontuacao, UsoPontuacaoAdmin)
