from .permissoes import usuario_tem_acesso_administrativo


def permissoes_do_usuario(request):
    return {
        'usuario_administrativo': usuario_tem_acesso_administrativo(request.user),
    }
