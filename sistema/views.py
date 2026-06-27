from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render

from .forms import MeusDadosForm


@login_required
def inicio_sistema(request):
    return render(request, 'inicio_sistema.html')


@login_required
def meus_dados(request):
    usuario = request.user
    try:
        perfil = usuario.perfil_administrativo
    except ObjectDoesNotExist:
        perfil = None

    if request.method == 'POST':
        form = MeusDadosForm(request.POST, usuario=usuario)
        if form.is_valid():
            senha_alterada = form.save()
            if senha_alterada:
                update_session_auth_hash(request, usuario)
            messages.success(request, 'Seus dados foram atualizados com sucesso.')
            return redirect('meus_dados')
        messages.error(request, 'Revise os campos antes de salvar.')
    else:
        form = MeusDadosForm(usuario=usuario)

    grupos = usuario.groups.order_by('name')
    return render(
        request,
        'meus_dados.html',
        {
            'form': form,
            'perfil': perfil,
            'grupos': grupos,
        },
    )
