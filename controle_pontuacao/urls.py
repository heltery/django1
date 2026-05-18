from django.urls import path

from .views import contato, dashboard, index, painel_administrativo

urlpatterns = [
    path('', index, name='index'),
    path('contato/', contato, name='contato'),
    path('dashboard/', dashboard, name='dashboard'),
    path('administrativo/', painel_administrativo, name='painel_administrativo'),
]
