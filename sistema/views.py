from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from .permissoes import usuario_tem_acesso_administrativo


@login_required
def inicio_sistema(request):
    return render(request, 'inicio_sistema.html')


def usuario_administrativo_required(view_func):
    return user_passes_test(
        usuario_tem_acesso_administrativo,
        login_url='login',
    )(view_func)


@usuario_administrativo_required
def painel_administrativo(request):
    return render(request, 'painel_administrativo.html')
