from datetime import date

from django import forms
from django.contrib.auth.models import Group, Permission, User

from controle_pontuacao.models import OcorrenciaVinculada, TipoOcorrencia, UsoPontuacao


class AdminFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'admin-field-control')


class PermissaoModelChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.content_type.app_label}.{obj.content_type.model} | {obj.name}'


class GrupoForm(AdminFormMixin, forms.Form):
    name = forms.CharField(label='Nome do grupo', max_length=150)
    permissions = PermissaoModelChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by(
            'content_type__app_label',
            'content_type__model',
            'codename',
        ),
        required=False,
        label='Permissoes',
        widget=forms.SelectMultiple(attrs={'size': 10}),
    )

    def save(self):
        grupo, _ = Group.objects.get_or_create(name=self.cleaned_data['name'])
        grupo.permissions.set(self.cleaned_data['permissions'])
        return grupo


class GrupoEditForm(GrupoForm):
    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        if instance and 'initial' not in kwargs:
            kwargs['initial'] = {
                'name': instance.name,
                'permissions': instance.permissions.all(),
            }
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        queryset = Group.objects.filter(name=name)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ja existe um grupo com este nome.')
        return name

    def save(self):
        grupo = self.instance
        grupo.name = self.cleaned_data['name']
        grupo.save()
        grupo.permissions.set(self.cleaned_data['permissions'])
        return grupo


class UsuarioForm(AdminFormMixin, forms.Form):
    username = forms.CharField(label='Usuario (matricula)', max_length=150)
    first_name = forms.CharField(label='Nome de guerra', max_length=150)
    whatsapp = forms.CharField(label='Telefone WhatsApp', max_length=150, required=False)
    email = forms.EmailField(label='E-mail', required=False)
    group = forms.ModelChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        label='Grupo',
    )
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ja existe um usuario com esta matricula.')
        return username

    def save(self, commit=True):
        usuario = User(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['whatsapp'],
            email=self.cleaned_data['email'],
        )
        usuario.set_password(self.cleaned_data['password'])
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            usuario.save()
            if self.cleaned_data['group']:
                usuario.groups.add(self.cleaned_data['group'])
        return usuario


class UsuarioEditForm(AdminFormMixin, forms.Form):
    username = forms.CharField(label='Usuario (matricula)', max_length=150)
    first_name = forms.CharField(label='Nome de guerra', max_length=150)
    whatsapp = forms.CharField(label='Telefone WhatsApp', max_length=150, required=False)
    email = forms.EmailField(label='E-mail', required=False)
    group = forms.ModelChoiceField(
        queryset=Group.objects.order_by('name'),
        required=False,
        label='Grupo',
    )
    password = forms.CharField(
        label='Senha',
        required=False,
        widget=forms.PasswordInput,
        help_text='Preencha somente se quiser trocar a senha.',
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        if instance and 'initial' not in kwargs:
            kwargs['initial'] = {
                'username': instance.username,
                'first_name': instance.first_name,
                'whatsapp': instance.last_name,
                'email': instance.email,
                'group': instance.groups.first(),
            }
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        queryset = User.objects.filter(username=username)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ja existe um usuario com esta matricula.')
        return username

    def save(self):
        usuario = self.instance
        usuario.username = self.cleaned_data['username']
        usuario.first_name = self.cleaned_data['first_name']
        usuario.last_name = self.cleaned_data['whatsapp']
        usuario.email = self.cleaned_data['email']
        if self.cleaned_data['password']:
            usuario.set_password(self.cleaned_data['password'])
        usuario.save()
        usuario.groups.clear()
        if self.cleaned_data['group']:
            usuario.groups.add(self.cleaned_data['group'])
        return usuario


class TipoOcorrenciaForm(AdminFormMixin, forms.ModelForm):
    class Meta:
        model = TipoOcorrencia
        fields = ('nome', 'descricao', 'pontuacao', 'ativo')
        widgets = {'descricao': forms.Textarea(attrs={'rows': 3})}


class UsuarioMatriculaNomeChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        nome_guerra = obj.first_name or 'Sem nome de guerra'
        return f'{obj.username} - {nome_guerra}'


class OcorrenciaVinculadaForm(AdminFormMixin, forms.Form):
    usuarios = UsuarioMatriculaNomeChoiceField(
        queryset=User.objects.none(),
        label='Usuarios',
        widget=forms.CheckboxSelectMultiple,
    )
    tipo = forms.ModelChoiceField(
        queryset=TipoOcorrencia.objects.filter(ativo=True).order_by('nome'),
        label='Tipo de ocorrencia',
    )
    pontuacao_aplicada = forms.IntegerField(
        label='Pontuacao aplicada',
        required=False,
        min_value=0,
    )
    observacao = forms.CharField(
        label='Observacao',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    data_ocorrencia = forms.DateField(
        label='Data da ocorrencia',
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, usuarios_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuarios'].queryset = (
            usuarios_queryset
            if usuarios_queryset is not None
            else User.objects.filter(is_active=True).order_by('username')
        )


class UsoPontuacaoForm(AdminFormMixin, forms.Form):
    usuarios = UsuarioMatriculaNomeChoiceField(
        queryset=User.objects.none(),
        label='Usuarios',
        widget=forms.CheckboxSelectMultiple,
    )
    descricao = forms.CharField(label='Descricao', max_length=200)
    pontos = forms.IntegerField(label='Pontos utilizados', min_value=1)
    data_uso = forms.DateField(
        label='Data de uso',
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, usuarios_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['usuarios'].queryset = (
            usuarios_queryset
            if usuarios_queryset is not None
            else User.objects.filter(is_active=True).order_by('username')
        )
