from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inicio_sistema(request):
    return render(request, 'inicio_sistema.html')
