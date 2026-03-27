from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.usuarios.models import Vehiculo

@login_required
def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, "transporte/lista.html", {
        "vehiculos": vehiculos
    })

@login_required
def crear_vehiculo(request):
    if request.method == "POST":
        Vehiculo.objects.create(
            placa=request.POST.get("placa"),
            tipo=request.POST.get("tipo"),
            capacidad=request.POST.get("capacidad"),
            estado="disponible"
        )
        return redirect("transporte:lista_vehiculos")
    return render(request, "transporte/form.html", {"action": "crear"})

@login_required
def editar_vehiculo(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    if request.method == "POST":
        vehiculo.placa = request.POST.get("placa")
        vehiculo.tipo = request.POST.get("tipo")
        vehiculo.capacidad = request.POST.get("capacidad")
        vehiculo.estado = request.POST.get("estado")
        vehiculo.save()
        return redirect("transporte:lista_vehiculos")
    return render(request, "transporte/form.html", {"vehiculo": vehiculo, "action": "editar"})

@login_required
def eliminar_vehiculo(request, id):
    vehiculo = get_object_or_404(Vehiculo, id=id)
    vehiculo.delete()
    return redirect("transporte:lista_vehiculos")
