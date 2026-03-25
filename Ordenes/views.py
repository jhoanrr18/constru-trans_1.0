from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Orden, Entrega
from usuarios.models import Usuario, Vehiculo, Material


# 📋 LISTAR ÓRDENES
@login_required
def lista_ordenes(request):

    ordenes = Orden.objects.all().order_by("-fecha")

    return render(request, "ordenes/lista_ordenes.html", {
        "ordenes": ordenes
    })


# ➕ CREAR ORDEN
@login_required
def crear_orden(request):

    clientes = Usuario.objects.filter(rol="cliente")
    conductores = Usuario.objects.filter(rol="conductor")

    if request.method == "POST":

        cliente_id = request.POST.get("cliente")
        conductor_id = request.POST.get("conductor")
        origen = request.POST.get("origen")
        destino = request.POST.get("destino")

        # validación básica
        if not cliente_id or not origen or not destino:
            return render(request, "ordenes/crear_orden.html", {
                "clientes": clientes,
                "conductores": conductores,
                "error": "Todos los campos son obligatorios"
            })

        Orden.objects.create(
            cliente_id=cliente_id,
            conductor_id=conductor_id if conductor_id else None,
            direccion_origen=origen,
            direccion_destino=destino
        )

        return redirect("lista_ordenes")

    return render(request, "ordenes/crear_orden.html", {
        "clientes": clientes,
        "conductores": conductores
    })


# 🚚 CREAR ENTREGA AUTOMÁTICA (SIN HTML)
def crear_entrega(request, orden_id):
    orden = Orden.objects.get(id=orden_id)

    conductores = Usuario.objects.filter(rol="conductor")
    vehiculos = Vehiculo.objects.all()

    if request.method == "POST":
        conductor_id = request.POST.get("conductor")
        vehiculo_id = request.POST.get("vehiculo")

        Entrega.objects.create(
            pedido=orden,
            conductor_id=conductor_id,
            vehiculo_id=vehiculo_id,
            fecha=orden.fecha
        )

        orden.estado = "en_ruta"
        orden.conductor_id = conductor_id
        orden.save()

        return redirect("lista_ordenes")

    return render(request, "ordenes/asignar_entrega.html", {
        "orden": orden,
        "conductores": conductores,
        "vehiculos": vehiculos
    })


@login_required
def editar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    clientes = Usuario.objects.filter(rol="cliente")
    conductores = Usuario.objects.filter(rol="conductor")

    if request.method == "POST":
        orden.cliente_id = request.POST.get("cliente") or orden.cliente_id
        orden.conductor_id = request.POST.get("conductor") or None
        orden.direccion_origen = request.POST.get("origen") or orden.direccion_origen
        orden.direccion_destino = request.POST.get("destino") or orden.direccion_destino
        orden.save()
        messages.success(request, "Orden actualizada correctamente")
        return redirect("lista_ordenes")

    return render(request, "ordenes/editar_orden.html", {
        "orden": orden,
        "clientes": clientes,
        "conductores": conductores
    })


@login_required
def eliminar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    if request.method == "POST":
        orden.delete()
        messages.success(request, "Orden eliminada correctamente")
        return redirect("lista_ordenes")
    
    return render(request, "ordenes/confirmar_eliminar.html", {"orden": orden})