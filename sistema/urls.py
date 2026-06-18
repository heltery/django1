from django.urls import path

from .views import (
    inicio_sistema,
    listar_grupos,
    listar_tipos_ocorrencia,
    listar_usuarios,
    painel_administrativo,
    listar_utilizacoes_pontos,
    registrar_utilizacao_pontos,
    vincular_ocorrencia,
)

urlpatterns = [
    path('sistema/', inicio_sistema, name='inicio_sistema'),
    path('administrativo/', painel_administrativo, name='painel_administrativo'),
    path('administrativo/grupos/', listar_grupos, name='listar_grupos'),
    path('administrativo/usuarios/', listar_usuarios, name='listar_usuarios'),
    path('administrativo/tipos-ocorrencia/', listar_tipos_ocorrencia, name='listar_tipos_ocorrencia'),
    path('administrativo/vincular-ocorrencia/', vincular_ocorrencia, name='vincular_ocorrencia'),
    path('administrativo/registrar-utilizacao/', registrar_utilizacao_pontos, name='registrar_utilizacao_pontos'),
    path('administrativo/utilizacoes/', listar_utilizacoes_pontos, name='listar_utilizacoes_pontos'),
]
