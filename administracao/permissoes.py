import unicodedata


def _normalizar_nome_grupo(nome):
    sem_acentos = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    return sem_acentos.casefold().strip()


def usuario_tem_acesso_administrativo(usuario):
    grupos_administrativos = {'administrativo', 'administracao'}

    return (
        usuario.is_authenticated
        and (
            usuario.is_superuser
            or any(
                _normalizar_nome_grupo(nome) in grupos_administrativos
                for nome in usuario.groups.values_list('name', flat=True)
            )
        )
    )
