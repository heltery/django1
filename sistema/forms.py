from django import forms
from django.contrib.auth import password_validation


class MeusDadosForm(forms.Form):
    whatsapp = forms.CharField(label='Telefone WhatsApp', max_length=150, required=False)
    email = forms.EmailField(label='E-mail', required=False)
    senha_atual = forms.CharField(
        label='Senha atual',
        required=False,
        widget=forms.PasswordInput,
        help_text='Preencha somente se quiser trocar a senha.',
    )
    nova_senha = forms.CharField(
        label='Nova senha',
        required=False,
        widget=forms.PasswordInput,
    )
    confirmar_senha = forms.CharField(
        label='Confirmar nova senha',
        required=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        if usuario and 'initial' not in kwargs:
            kwargs['initial'] = {
                'whatsapp': usuario.last_name,
                'email': usuario.email,
            }
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'admin-field-control')

    def clean(self):
        cleaned_data = super().clean()
        senha_atual = cleaned_data.get('senha_atual')
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        quer_trocar_senha = senha_atual or nova_senha or confirmar_senha
        if not quer_trocar_senha:
            return cleaned_data

        if not senha_atual:
            self.add_error('senha_atual', 'Informe sua senha atual.')
        elif self.usuario and not self.usuario.check_password(senha_atual):
            self.add_error('senha_atual', 'Senha atual incorreta.')

        if not nova_senha:
            self.add_error('nova_senha', 'Informe a nova senha.')
        if not confirmar_senha:
            self.add_error('confirmar_senha', 'Confirme a nova senha.')
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas nao conferem.')
        if nova_senha and self.usuario:
            try:
                password_validation.validate_password(nova_senha, self.usuario)
            except forms.ValidationError as error:
                self.add_error('nova_senha', error)

        return cleaned_data

    def save(self):
        usuario = self.usuario
        usuario.last_name = self.cleaned_data['whatsapp']
        usuario.email = self.cleaned_data['email']

        senha_alterada = bool(self.cleaned_data.get('nova_senha'))
        if senha_alterada:
            usuario.set_password(self.cleaned_data['nova_senha'])

        usuario.save()
        return senha_alterada
