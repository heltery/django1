from django.urls import path

from .views import contato, dashboard, index

urlpatterns = [
    path('', index, name='index'),
    path('contato/', contato, name='contato'),
    path('dashboard/', dashboard, name='dashboard'),
]
