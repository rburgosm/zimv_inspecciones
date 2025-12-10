from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Auditor
from .forms import AuditorForm


@login_required
def lista_auditores(request):
    """Lista de auditores"""
    auditores = Auditor.objects.all().order_by('nombre', 'apellidos')
    return render(request, 'auditores/lista.html', {'auditores': auditores})


@login_required
def crear_auditor(request):
    """Crear nuevo auditor"""
    if request.method == 'POST':
        form = AuditorForm(request.POST)
        if form.is_valid():
            auditor = form.save(commit=False)
            auditor.usuario_creacion = request.user
            auditor.save()
            messages.success(request, 'Auditor creado correctamente')
            return redirect('auditores:lista')
    else:
        form = AuditorForm()
    
    return render(request, 'auditores/form.html', {'form': form, 'titulo': 'Crear Auditor'})


@login_required
def editar_auditor(request, pk):
    """Editar auditor existente"""
    auditor = get_object_or_404(Auditor, pk=pk)
    
    if request.method == 'POST':
        form = AuditorForm(request.POST, instance=auditor)
        if form.is_valid():
            auditor = form.save(commit=False)
            auditor.usuario_actualizacion = request.user
            auditor.save()
            messages.success(request, 'Auditor actualizado correctamente')
            return redirect('auditores:lista')
    else:
        form = AuditorForm(instance=auditor)
    
    return render(request, 'auditores/form.html', {'form': form, 'titulo': 'Editar Auditor', 'auditor': auditor})
