from django.urls import path

from .views import (
    listar_grupos,
    listar_ocorrencias_vinculadas,
    listar_tipos_ocorrencia,
    listar_usuarios,
    listar_utilizacoes_pontos,
    painel_administrativo,
    registrar_utilizacao_pontos,
    vincular_ocorrencia,
)

urlpatterns = [
    path('administrativo/', painel_administrativo, name='painel_administrativo'),
    path('administrativo/grupos/', listar_grupos, name='listar_grupos'),
    path('administrativo/usuarios/', listar_usuarios, name='listar_usuarios'),
    path('administrativo/tipos-ocorrencia/', listar_tipos_ocorrencia, name='listar_tipos_ocorrencia'),
    path('administrativo/ocorrencias/', listar_ocorrencias_vinculadas, name='listar_ocorrencias_vinculadas'),
    path('administrativo/vincular-ocorrencia/', vincular_ocorrencia, name='vincular_ocorrencia'),
    path('administrativo/registrar-utilizacao/', registrar_utilizacao_pontos, name='registrar_utilizacao_pontos'),
    path('administrativo/utilizacoes/', listar_utilizacoes_pontos, name='listar_utilizacoes_pontos'),
]
