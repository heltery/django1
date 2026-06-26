from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('posto_graduacao', models.CharField(blank=True, choices=[('SD', 'SD'), ('CB', 'CB'), ('3º SGT', '3º SGT'), ('2º SGT', '2º SGT'), ('1º SGT', '1º SGT'), ('ST', 'ST'), ('2º TEN', '2º TEN'), ('1º TEN', '1º TEN'), ('CAP', 'CAP'), ('MAJ', 'MAJ'), ('TC', 'TC'), ('CEL', 'CEL')], max_length=20, verbose_name='Posto/Graduação')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_administrativo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'perfil de usuario',
                'verbose_name_plural': 'perfis de usuarios',
            },
        ),
    ]
