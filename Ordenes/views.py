from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Orden
from usuarios.models import Usuario


@login_required
def lista_ordenes(request):

    ordenes = Orden.objects.all()

    return render(request, "Ordenes/lista_ordenes.html", {
        "ordenes": ordenes
    })


@login_required
def crear_orden(request):

    clientes = Usuario.objects.filter(rol="cliente")
    conductores = Usuario.objects.filter(rol="conductor")

    if request.method == "POST":

        cliente = request.POST.get("cliente")
        conductor = request.POST.get("conductor")
        origen = request.POST.get("origen")
        destino = request.POST.get("destino")

        Orden.objects.create(
            cliente_id=cliente,
            conductor_id=conductor,
            direccion_origen=origen,
            direccion_destino=destino
        )

        return redirect("lista_ordenes")

    return render(request, "Ordenes/crear_orden.html", {
        "clientes": clientes,
        "conductores": conductores
    })


@login_required
def ver_orden(request, id):
    orden = get_object_or_404(Orden, pk=id)
    return render(request, "Ordenes/ver_orden.html", {"orden": orden})


@login_required
def editar_orden(request, id):
    orden = get_object_or_404(Orden, pk=id)
    clientes = Usuario.objects.filter(rol="cliente")
    conductores = Usuario.objects.filter(rol="conductor")

    if request.method == 'POST':
        orden.cliente_id = request.POST.get('cliente')
        orden.conductor_id = request.POST.get('conductor')
        orden.direccion_origen = request.POST.get('origen')
        orden.direccion_destino = request.POST.get('destino')
        orden.estado = request.POST.get('estado')
        orden.save()
        messages.success(request, 'Orden actualizada correctamente')
        return redirect('lista_ordenes')

    return render(request, 'Ordenes/editar_orden.html', {
        'orden': orden,
        'clientes': clientes,
        'conductores': conductores,
        'estados': ['pendiente', 'en_ruta', 'entregado'],
    })


@login_required
def asignar_conductor(request, id):
    orden = get_object_or_404(Orden, pk=id)
    conductores = Usuario.objects.filter(rol='conductor')

    if request.method == 'POST':
        conductor_id = request.POST.get('conductor')
        orden.conductor_id = conductor_id
        orden.save()
        messages.success(request, 'Conductor asignado correctamente')
        return redirect('lista_ordenes')

    return render(request, 'Ordenes/asignar_conductor.html', {
        'orden': orden,
        'conductores': conductores,
    })


@login_required
def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, pk=id)
    orden.delete()
    messages.success(request, 'Orden eliminada correctamente')
    return redirect('lista_ordenes')
