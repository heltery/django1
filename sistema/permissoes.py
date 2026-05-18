def usuario_tem_acesso_administrativo(usuario):
    return (
        usuario.is_authenticated
        and (
            usuario.is_staff
            or usuario.is_superuser
            or usuario.groups.filter(name='Administrativo').exists()
        )
    )
