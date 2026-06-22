from django.urls import path

from .views import inicio_sistema

urlpatterns = [
    path('sistema/', inicio_sistema, name='inicio_sistema'),
]
