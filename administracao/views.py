from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import redirect, render

from banco_de_horas.models import OcorrenciaVinculada, TipoOcorrencia, UsoPontuacao, saldo_usuario

from .forms import (
    GrupoEditForm,
    GrupoForm,
    OcorrenciaVinculadaForm,
    TipoOcorrenciaForm,
    UsoPontuacaoForm,
    UsuarioEditForm,
    UsuarioForm,
)
from .permissoes import usuario_tem_acesso_administrativo


def usuario_administrativo_required(view_func):
    return user_passes_test(
        usuario_tem_acesso_administrativo,
        login_url='login',
    )(view_func)


@usuario_administrativo_required
def painel_administrativo(request):
    forms = {
        'grupo': GrupoForm(prefix='grupo'),
        'usuario': UsuarioForm(prefix='usuario'),
        'tipo': TipoOcorrenciaForm(prefix='tipo'),
        'ocorrencia': OcorrenciaVinculadaForm(prefix='ocorrencia'),
        'uso': UsoPontuacaoForm(prefix='uso'),
    }

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        form_class = {
            'grupo': GrupoForm,
            'usuario': UsuarioForm,
            'tipo': TipoOcorrenciaForm,
            'ocorrencia': OcorrenciaVinculadaForm,
            'uso': UsoPontuacaoForm,
        }.get(form_type)

        if form_class:
            form = form_class(request.POST, prefix=form_type)
            forms[form_type] = form

            if form.is_valid():
                if form_type == 'grupo':
                    form.save()
                    messages.success(request, 'Grupo salvo com permissoes atualizadas.')
                elif form_type == 'usuario':
                    form.save()
                    messages.success(request, 'Usuario criado com sucesso.')
                elif form_type == 'tipo':
                    form.save()
                    messages.success(request, 'Tipo de ocorrencia criado com sucesso.')
                elif form_type == 'ocorrencia':
                    usuarios = form.cleaned_data['usuarios']
                    tipo = form.cleaned_data['tipo']
                    pontuacao = form.cleaned_data['pontuacao_aplicada']
                    for usuario in usuarios:
                        OcorrenciaVinculada.objects.create(
                            usuario=usuario,
                            tipo=tipo,
                            pontuacao_aplicada=pontuacao,
                            observacao=form.cleaned_data['observacao'],
                            data_ocorrencia=form.cleaned_data['data_ocorrencia'],
                            criado_por=request.user,
                        )
                    messages.success(request, 'Ocorrencia vinculada aos usuarios selecionados.')
                elif form_type == 'uso':
                    for usuario in form.cleaned_data['usuarios']:
                        UsoPontuacao.objects.create(
                            usuario=usuario,
                            descricao=form.cleaned_data['descricao'],
                            pontos=form.cleaned_data['pontos'],
                            data_uso=form.cleaned_data['data_uso'],
                            registrado_por=request.user,
                        )
                    messages.success(request, 'Uso de pontos registrado para os usuarios selecionados.')
                return redirect('painel_administrativo')

            messages.error(request, 'Revise os campos destacados antes de salvar.')

    contexto = {
        'forms': forms,
        'tipos': TipoOcorrencia.objects.order_by('nome')[:8],
        'ocorrencias': OcorrenciaVinculada.objects.select_related('usuario', 'tipo').all()[:8],
        'usos': UsoPontuacao.objects.select_related('usuario').all()[:8],
    }
    return render(request, 'painel_administrativo.html', contexto)


@usuario_administrativo_required
def listar_grupos(request):
    grupo_edit_form_com_erro = None
    grupo_em_edicao = request.GET.get('editar')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'grupo_edit':
            grupo = Group.objects.filter(pk=request.POST.get('grupo_id')).first()
            if grupo:
                form = GrupoEditForm(request.POST, prefix=f'grupo_edit_{grupo.pk}', instance=grupo)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Grupo atualizado com sucesso.')
                    return redirect('listar_grupos')
                grupo_edit_form_com_erro = (grupo.pk, form)
                messages.error(request, 'Revise os campos do grupo antes de salvar.')
            else:
                messages.error(request, 'Grupo nao encontrado.')

        elif form_type == 'grupo_delete':
            grupo = Group.objects.filter(pk=request.POST.get('grupo_id')).first()
            if grupo:
                nome = grupo.name
                grupo.delete()
                messages.success(request, f'Grupo {nome} excluido com sucesso.')
            else:
                messages.error(request, 'Grupo nao encontrado.')
            return redirect('listar_grupos')

    grupos = list(Group.objects.prefetch_related('permissions').order_by('name'))
    for grupo in grupos:
        if grupo_edit_form_com_erro and grupo_edit_form_com_erro[0] == grupo.pk:
            grupo.edit_form = grupo_edit_form_com_erro[1]
            grupo.editando = True
        else:
            grupo.edit_form = GrupoEditForm(prefix=f'grupo_edit_{grupo.pk}', instance=grupo)
            grupo.editando = str(grupo.pk) == grupo_em_edicao

    return render(request, 'grupos_administrativos.html', {'grupos': grupos})


@usuario_administrativo_required
def listar_usuarios(request):
    usuario_edit_form_com_erro = None
    usuario_em_edicao = request.GET.get('editar')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'usuario_edit':
            usuario = User.objects.filter(pk=request.POST.get('usuario_id')).first()
            if usuario:
                form = UsuarioEditForm(request.POST, prefix=f'usuario_edit_{usuario.pk}', instance=usuario)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Usuario atualizado com sucesso.')
                    return redirect('listar_usuarios')
                usuario_edit_form_com_erro = (usuario.pk, form)
                messages.error(request, 'Revise os campos do usuario antes de salvar.')
            else:
                messages.error(request, 'Usuario nao encontrado.')

        elif form_type == 'usuario_delete':
            usuario = User.objects.filter(pk=request.POST.get('usuario_id')).first()
            if usuario == request.user:
                messages.error(request, 'Voce nao pode excluir seu proprio usuario.')
            elif usuario:
                matricula = usuario.username
                usuario.delete()
                messages.success(request, f'Usuario {matricula} excluido com sucesso.')
            else:
                messages.error(request, 'Usuario nao encontrado.')
            return redirect('listar_usuarios')

    usuarios = list(User.objects.prefetch_related('groups').order_by('username'))
    for usuario in usuarios:
        #usuario.saldo_atual = saldo_usuario(usuario)
        if usuario_edit_form_com_erro and usuario_edit_form_com_erro[0] == usuario.pk:
            usuario.edit_form = usuario_edit_form_com_erro[1]
            usuario.editando = True
        else:
            usuario.edit_form = UsuarioEditForm(prefix=f'usuario_edit_{usuario.pk}', instance=usuario)
            usuario.editando = str(usuario.pk) == usuario_em_edicao

    return render(request, 'usuarios_administrativos.html', {'usuarios': usuarios})


@usuario_administrativo_required
def listar_tipos_ocorrencia(request):
    tipo_edit_form_com_erro = None
    tipo_em_edicao = request.GET.get('editar')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'tipo_edit':
            tipo = TipoOcorrencia.objects.filter(pk=request.POST.get('tipo_id')).first()
            if tipo:
                form = TipoOcorrenciaForm(request.POST, prefix=f'tipo_edit_{tipo.pk}', instance=tipo)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Tipo de ocorrencia atualizado com sucesso.')
                    return redirect('listar_tipos_ocorrencia')
                tipo_edit_form_com_erro = (tipo.pk, form)
                messages.error(request, 'Revise os campos do tipo de ocorrencia antes de salvar.')
            else:
                messages.error(request, 'Tipo de ocorrencia nao encontrado.')

        elif form_type == 'tipo_delete':
            tipo = TipoOcorrencia.objects.filter(pk=request.POST.get('tipo_id')).first()
            if tipo:
                nome = tipo.nome
                try:
                    tipo.delete()
                    messages.success(request, f'Tipo de ocorrencia {nome} excluido com sucesso.')
                except ProtectedError:
                    messages.error(
                        request,
                        f'Tipo de ocorrencia {nome} nao pode ser excluido porque ja possui ocorrencias vinculadas.',
                    )
            else:
                messages.error(request, 'Tipo de ocorrencia nao encontrado.')
            return redirect('listar_tipos_ocorrencia')

    tipos = list(TipoOcorrencia.objects.order_by('nome'))
    for tipo in tipos:
        if tipo_edit_form_com_erro and tipo_edit_form_com_erro[0] == tipo.pk:
            tipo.edit_form = tipo_edit_form_com_erro[1]
            tipo.editando = True
        else:
            tipo.edit_form = TipoOcorrenciaForm(prefix=f'tipo_edit_{tipo.pk}', instance=tipo)
            tipo.editando = str(tipo.pk) == tipo_em_edicao

    return render(request, 'tipos_ocorrencia_administrativos.html', {'tipos': tipos})


@usuario_administrativo_required
def vincular_ocorrencia(request):
    busca = request.GET.get('q', '').strip()
    usuarios_queryset = User.objects.filter(is_active=True).order_by('username')
    if busca:
        usuarios_queryset = usuarios_queryset.filter(
            Q(username__icontains=busca)
            | Q(first_name__icontains=busca)
        )

    form = OcorrenciaVinculadaForm(usuarios_queryset=usuarios_queryset)

    if request.method == 'POST':
        form = OcorrenciaVinculadaForm(request.POST, usuarios_queryset=usuarios_queryset)
        if form.is_valid():
            usuarios = form.cleaned_data['usuarios']
            tipo = form.cleaned_data['tipo']
            pontuacao = form.cleaned_data['pontuacao_aplicada']
            for usuario in usuarios:
                OcorrenciaVinculada.objects.create(
                    usuario=usuario,
                    tipo=tipo,
                    pontuacao_aplicada=pontuacao,
                    observacao=form.cleaned_data['observacao'],
                    data_ocorrencia=form.cleaned_data['data_ocorrencia'],
                    criado_por=request.user,
                )
            messages.success(request, 'Ocorrencia vinculada aos militares selecionados.')
            return redirect('vincular_ocorrencia')

        messages.error(request, 'Revise os campos destacados antes de salvar.')

    tipos_pontuacao = {
        str(tipo.pk): tipo.pontuacao
        for tipo in TipoOcorrencia.objects.filter(ativo=True)
    }
    contexto = {
        'busca': busca,
        'form': form,
        'usuarios_encontrados': usuarios_queryset.exists(),
        'tipos_pontuacao': tipos_pontuacao,
        'ocorrencias': OcorrenciaVinculada.objects.select_related('usuario', 'tipo').all()[:8],
    }
    return render(request, 'vincular_ocorrencia.html', contexto)


@usuario_administrativo_required
def registrar_utilizacao_pontos(request):
    busca = request.GET.get('q', '').strip()
    usuarios_queryset = User.objects.filter(is_active=True).order_by('username')
    if busca:
        usuarios_queryset = usuarios_queryset.filter(
            Q(username__icontains=busca)
            | Q(first_name__icontains=busca)
        )

    form = UsoPontuacaoForm(usuarios_queryset=usuarios_queryset)

    if request.method == 'POST':
        form = UsoPontuacaoForm(request.POST, usuarios_queryset=usuarios_queryset)
        if form.is_valid():
            for usuario in form.cleaned_data['usuarios']:
                UsoPontuacao.objects.create(
                    usuario=usuario,
                    descricao=form.cleaned_data['descricao'],
                    pontos=form.cleaned_data['pontos'],
                    data_uso=form.cleaned_data['data_uso'],
                    registrado_por=request.user,
                )
            messages.success(request, 'Uso de pontos registrado para os militares selecionados.')
            return redirect('registrar_utilizacao_pontos')

        messages.error(request, 'Revise os campos destacados antes de salvar.')

    contexto = {
        'busca': busca,
        'form': form,
        'usuarios_encontrados': usuarios_queryset.exists(),
        'usos': UsoPontuacao.objects.select_related('usuario').all()[:8],
    }
    return render(request, 'registrar_utilizacao_pontos.html', contexto)


@usuario_administrativo_required
def listar_utilizacoes_pontos(request):
    busca = request.GET.get('q', '').strip()
    usos = UsoPontuacao.objects.select_related('usuario').order_by('-data_uso', '-criado_em')
    if busca:
        usos = usos.filter(
            Q(usuario__username__icontains=busca)
            | Q(usuario__first_name__icontains=busca)
        )

    contexto = {
        'busca': busca,
        'usos': usos,
    }
    return render(request, 'utilizacoes_pontos_administrativas.html', contexto)
