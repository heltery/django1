from django.db import models
from django.conf import settings
from django.db.models import Sum


class TipoOcorrencia(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True)
    pontuacao = models.PositiveIntegerField()
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'tipo de ocorrencia'
        verbose_name_plural = 'tipos de ocorrencia'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.pontuacao} pts)'


class OcorrenciaVinculada(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ocorrencias_vinculadas',
    )
    tipo = models.ForeignKey(
        TipoOcorrencia,
        on_delete=models.PROTECT,
        related_name='ocorrencias',
    )
    pontuacao_aplicada = models.PositiveIntegerField(blank=True, null=True)
    observacao = models.TextField(blank=True)
    data_ocorrencia = models.DateField()
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='ocorrencias_criadas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ocorrencia vinculada'
        verbose_name_plural = 'ocorrencias vinculadas'
        ordering = ['-data_ocorrencia', '-criado_em']

    def save(self, *args, **kwargs):
        if self.pontuacao_aplicada is None:
            self.pontuacao_aplicada = self.tipo.pontuacao
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.usuario} - {self.tipo.nome} (+{self.pontuacao_aplicada} pts)'


class UsoPontuacao(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usos_pontuacao',
    )
    descricao = models.CharField(max_length=200)
    pontos = models.PositiveIntegerField()
    data_uso = models.DateField()
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usos_registrados',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'uso de pontuacao'
        verbose_name_plural = 'usos de pontuacao'
        ordering = ['-data_uso', '-criado_em']

    def __str__(self):
        return f'{self.usuario} - {self.descricao} (-{self.pontos} pts)'


def saldo_usuario(usuario):
    ganhos = usuario.ocorrencias_vinculadas.aggregate(total=Sum('pontuacao_aplicada'))['total'] or 0
    usos = usuario.usos_pontuacao.aggregate(total=Sum('pontos'))['total'] or 0
    return ganhos - usos
