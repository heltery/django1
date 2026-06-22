from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria os grupos Administrativo e Operacional com permissoes iniciais.'

    def handle(self, *args, **options):
        administrativo, _ = Group.objects.get_or_create(name='Administrativo')
        operacional, _ = Group.objects.get_or_create(name='Operacional')

        permissoes_administrativas = Permission.objects.filter(
            content_type__app_label__in=['auth', 'core'],
            codename__in=[
                'add_user',
                'change_user',
                'view_user',
                'add_group',
                'change_group',
                'view_group',
                'add_tipoocorrencia',
                'change_tipoocorrencia',
                'delete_tipoocorrencia',
                'view_tipoocorrencia',
                'add_ocorrenciavinculada',
                'change_ocorrenciavinculada',
                'delete_ocorrenciavinculada',
                'view_ocorrenciavinculada',
                'add_usopontuacao',
                'change_usopontuacao',
                'delete_usopontuacao',
                'view_usopontuacao',
            ],
        )

        administrativo.permissions.set(permissoes_administrativas)
        operacional.permissions.clear()

        self.stdout.write(self.style.SUCCESS('Grupos preparados com sucesso.'))
