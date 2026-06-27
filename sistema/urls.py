from django.urls import path

from .views import inicio_sistema, meus_dados

urlpatterns = [
    path('sistema/', inicio_sistema, name='inicio_sistema'),
    path('meus-dados/', meus_dados, name='meus_dados'),
]
