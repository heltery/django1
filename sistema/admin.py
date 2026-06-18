from django.contrib import admin

# AQUI É OS TITULOS DOS MENUS ADMINISTRATIVOS DO DJANGO

admin.site.site_header = 'Administracao do Sistema BPRONE'
admin.site.site_title = 'Sistema'
admin.site.index_title = 'Painel administrativo'


def somente_superuser(request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = somente_superuser
