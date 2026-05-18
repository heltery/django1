from django.urls import path

from .views import inicio_sistema, painel_administrativo

urlpatterns = [
    path('sistema/', inicio_sistema, name='inicio_sistema'),
    path('administrativo/', painel_administrativo, name='painel_administrativo'),
]
