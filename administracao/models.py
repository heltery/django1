from django.conf import settings
from django.db import models


POSTOS_GRADUACOES = [
    ('SD', 'SD'),
    ('CB', 'CB'),
    ('3º SGT', '3º SGT'),
    ('2º SGT', '2º SGT'),
    ('1º SGT', '1º SGT'),
    ('ST', 'ST'),
    ('2º TEN', '2º TEN'),
    ('1º TEN', '1º TEN'),
    ('CAP', 'CAP'),
    ('MAJ', 'MAJ'),
    ('TC', 'TC'),
    ('CEL', 'CEL'),
]


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_administrativo',
    )
    posto_graduacao = models.CharField(
        'Posto/Graduação',
        max_length=20,
        choices=POSTOS_GRADUACOES,
        blank=True,
    )

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfis de usuarios'

    def __str__(self):
        return f'{self.usuario} - {self.posto_graduacao or "Sem posto/graduacao"}'
