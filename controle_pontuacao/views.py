from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from .models import saldo_usuario


def index(request):
    return render(request, 'index.html')


def contato(request):
    return render(request, 'contato.html')


@login_required
def dashboard(request):
    grupos = request.user.groups.values_list('name', flat=True)
    ultimos_ganhos = request.user.ocorrencias_vinculadas.select_related('tipo')[:5]
    ultimos_usos = request.user.usos_pontuacao.all()[:5]
    return render(request, 'dashboard.html', {
        'grupos': grupos,
        'saldo': saldo_usuario(request.user),
        'ultimos_ganhos': ultimos_ganhos,
        'ultimos_usos': ultimos_usos,
    })


def pertence_ao_grupo(nome_grupo):
    return user_passes_test(
        lambda user: user.is_authenticated and user.groups.filter(name=nome_grupo).exists(),
        login_url='login',
    )


@pertence_ao_grupo('Administrativo')
def painel_administrativo(request):
    return render(request, 'painel_administrativo.html')
