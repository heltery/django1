from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from django.db.models import Q
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_date

from banco_de_horas.models import OcorrenciaVinculada, TipoOcorrencia, UsoPontuacao

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


def identificacao_militar(usuario):
    try:
        perfil = usuario.perfil_administrativo
    except ObjectDoesNotExist:
        perfil = None
    posto_graduacao = perfil.posto_graduacao if perfil and perfil.posto_graduacao else ''
    nome_guerra = usuario.first_name or 'Sem nome de guerra'
    return f'{posto_graduacao} {nome_guerra}'.strip()


def aplicar_identificacao_militar(usuarios):
    for usuario in usuarios:
        usuario.identificacao_militar = identificacao_militar(usuario)
    return usuarios


def usuario_administrativo_required(view_func):
    return user_passes_test(
        usuario_tem_acesso_administrativo,
        login_url='login',
    )(view_func)


def ids_usuarios_selecionados(request):
    origem = request.POST if request.method == 'POST' else request.GET
    return [
        usuario_id
        for usuario_id in origem.getlist('usuarios')
        if usuario_id.isdigit()
    ]


def usuarios_para_selecao(request):
    busca = request.GET.get('q', '').strip()
    selecionados = ids_usuarios_selecionados(request)

    usuarios_queryset = User.objects.select_related('perfil_administrativo').filter(
        is_active=True,
    ).order_by('first_name', 'username')
    if busca:
        usuarios_queryset = usuarios_queryset.filter(
            Q(username__icontains=busca)
            | Q(first_name__icontains=busca)
            | Q(perfil_administrativo__posto_graduacao__icontains=busca)
        )

    usuarios_selecionados = User.objects.select_related('perfil_administrativo').filter(
        is_active=True,
        pk__in=selecionados,
    ).order_by('first_name', 'username')

    return busca, selecionados, usuarios_queryset, usuarios_selecionados, usuarios_queryset.exists()


@usuario_administrativo_required
def painel_administrativo(request):
    forms = {
        'grupo': GrupoForm(prefix='grupo'),
        'usuario': UsuarioForm(prefix='usuario'),
        'tipo': TipoOcorrenciaForm(prefix='tipo'),
    }

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        form_class = {
            'grupo': GrupoForm,
            'usuario': UsuarioForm,
            'tipo': TipoOcorrenciaForm,
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
                return redirect('painel_administrativo')

            messages.error(request, 'Revise os campos destacados antes de salvar.')

    contexto = {
        'forms': forms,
        'tipos': TipoOcorrencia.objects.order_by('nome')[:8],
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
    busca = request.GET.get('q', '').strip()
    filtro = request.GET.get('filtro', 'todos')
    filtros_usuarios = {
        'todos': 'Todos',
        'matricula': 'Matricula',
        'posto': 'Posto/Graduacao',
        'nome': 'Nome de guerra',
        'grupo': 'Grupo',
    }
    if filtro not in filtros_usuarios:
        filtro = 'todos'

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

    usuarios_queryset = User.objects.select_related('perfil_administrativo').prefetch_related('groups').order_by(
        'first_name',
        'username',
    )
    if busca:
        filtros_query = {
            'todos': (
                Q(username__icontains=busca)
                | Q(first_name__icontains=busca)
                | Q(email__icontains=busca)
                | Q(last_name__icontains=busca)
                | Q(groups__name__icontains=busca)
                | Q(perfil_administrativo__posto_graduacao__icontains=busca)
            ),
            'matricula': Q(username__icontains=busca),
            'posto': Q(perfil_administrativo__posto_graduacao__icontains=busca),
            'nome': Q(first_name__icontains=busca),
            'whatsapp': Q(last_name__icontains=busca),
            'email': Q(email__icontains=busca),
            'grupo': Q(groups__name__icontains=busca),
        }
        usuarios_queryset = usuarios_queryset.filter(filtros_query[filtro]).distinct()

    paginator = Paginator(usuarios_queryset, 25)
    pagina = paginator.get_page(request.GET.get('page'))
    usuarios = list(pagina.object_list)
    usuarios_ids = [usuario.pk for usuario in usuarios]

    ganhos_por_usuario = {
        item['usuario_id']: item['total'] or 0
        for item in OcorrenciaVinculada.objects.filter(usuario_id__in=usuarios_ids)
        .values('usuario_id')
        .annotate(total=Sum('pontuacao_aplicada'))
    }
    usos_por_usuario = {
        item['usuario_id']: item['total'] or 0
        for item in UsoPontuacao.objects.filter(usuario_id__in=usuarios_ids)
        .values('usuario_id')
        .annotate(total=Sum('pontos'))
    }

    for usuario in usuarios:
        usuario.identificacao_militar = identificacao_militar(usuario)
        usuario.saldo_atual = ganhos_por_usuario.get(usuario.pk, 0) - usos_por_usuario.get(usuario.pk, 0)
        if usuario_edit_form_com_erro and usuario_edit_form_com_erro[0] == usuario.pk:
            usuario.edit_form = usuario_edit_form_com_erro[1]
            usuario.editando = True
        else:
            usuario.edit_form = UsuarioEditForm(prefix=f'usuario_edit_{usuario.pk}', instance=usuario)
            usuario.editando = str(usuario.pk) == usuario_em_edicao

    return render(
        request,
        'usuarios_administrativos.html',
        {
            'busca': busca,
            'filtro': filtro,
            'filtros_usuarios': filtros_usuarios,
            'pagina': pagina,
            'usuarios': usuarios,
        },
    )


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
    busca, usuarios_selecionados, usuarios_queryset, usuarios_selecionados_objetos, usuarios_encontrados = usuarios_para_selecao(request)
    usuarios = aplicar_identificacao_militar(list(usuarios_queryset))
    usuarios_selecionados_objetos = aplicar_identificacao_militar(list(usuarios_selecionados_objetos))
    usuarios_selecionados_set = set(usuarios_selecionados)
    for usuario in usuarios:
        usuario.selecionado = str(usuario.pk) in usuarios_selecionados_set

    form = OcorrenciaVinculadaForm(
        usuarios_queryset=usuarios_queryset,
        initial={'usuarios': usuarios_selecionados},
    )

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
        'usuarios_selecionados': usuarios_selecionados,
        'usuarios_selecionados_objetos': usuarios_selecionados_objetos,
        'usuarios': usuarios,
        'form': form,
        'usuarios_encontrados': usuarios_encontrados,
        'tipos_pontuacao': tipos_pontuacao,
    }
    return render(request, 'vincular_ocorrencia.html', contexto)


@usuario_administrativo_required
def registrar_utilizacao_pontos(request):
    busca, usuarios_selecionados, usuarios_queryset, usuarios_selecionados_objetos, usuarios_encontrados = usuarios_para_selecao(request)
    usuarios = aplicar_identificacao_militar(list(usuarios_queryset))
    usuarios_selecionados_objetos = aplicar_identificacao_militar(list(usuarios_selecionados_objetos))
    usuarios_selecionados_set = set(usuarios_selecionados)
    for usuario in usuarios:
        usuario.selecionado = str(usuario.pk) in usuarios_selecionados_set

    form = UsoPontuacaoForm(
        usuarios_queryset=usuarios_queryset,
        initial={'usuarios': usuarios_selecionados},
    )

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
        'usuarios_selecionados': usuarios_selecionados,
        'usuarios_selecionados_objetos': usuarios_selecionados_objetos,
        'usuarios': usuarios,
        'form': form,
        'usuarios_encontrados': usuarios_encontrados,
    }
    return render(request, 'registrar_utilizacao_pontos.html', contexto)


@usuario_administrativo_required
def listar_ocorrencias_vinculadas(request):
    filtros = {
        'matricula': request.GET.get('matricula', '').strip(),
        'nome': request.GET.get('nome', '').strip(),
        'tipo': request.GET.get('tipo', '').strip(),
        'data': request.GET.get('data', '').strip(),
    }
    ocorrencias = OcorrenciaVinculada.objects.select_related('usuario', 'tipo').order_by(
        '-data_ocorrencia',
        '-criado_em',
    )
    if filtros['matricula']:
        ocorrencias = ocorrencias.filter(usuario__username__icontains=filtros['matricula'])
    if filtros['nome']:
        ocorrencias = ocorrencias.filter(usuario__first_name__icontains=filtros['nome'])
    if filtros['tipo']:
        ocorrencias = ocorrencias.filter(tipo_id=filtros['tipo'])
    data = parse_date(filtros['data']) if filtros['data'] else None
    if data:
        ocorrencias = ocorrencias.filter(data_ocorrencia=data)

    pagina = Paginator(ocorrencias, 25).get_page(request.GET.get('page'))
    query = request.GET.copy()
    query.pop('page', None)

    contexto = {
        'filtros': filtros,
        'pagina': pagina,
        'querystring': query.urlencode(),
        'tipos': TipoOcorrencia.objects.order_by('nome'),
    }
    return render(request, 'ocorrencias_administrativas.html', contexto)


@usuario_administrativo_required
def listar_utilizacoes_pontos(request):
    filtros = {
        'matricula': request.GET.get('matricula', '').strip(),
        'nome': request.GET.get('nome', '').strip(),
        'data': request.GET.get('data', '').strip(),
    }
    usos = UsoPontuacao.objects.select_related('usuario').order_by('-data_uso', '-criado_em')
    if filtros['matricula']:
        usos = usos.filter(usuario__username__icontains=filtros['matricula'])
    if filtros['nome']:
        usos = usos.filter(usuario__first_name__icontains=filtros['nome'])
    data = parse_date(filtros['data']) if filtros['data'] else None
    if data:
        usos = usos.filter(data_uso=data)

    pagina = Paginator(usos, 25).get_page(request.GET.get('page'))
    query = request.GET.copy()
    query.pop('page', None)

    contexto = {
        'filtros': filtros,
        'pagina': pagina,
        'querystring': query.urlencode(),
    }
    return render(request, 'utilizacoes_pontos_administrativas.html', contexto)
