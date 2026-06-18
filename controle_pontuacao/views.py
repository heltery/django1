from django.contrib.auth.decorators import login_required
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
