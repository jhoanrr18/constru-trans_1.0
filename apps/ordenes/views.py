from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Orden, Entrega
from apps.usuarios.models import Usuario, Vehiculo, Material

@login_required
def lista_pedidos_admin(request):
    pedidos = Orden.objects.all().order_by("-fecha")
    
    cliente_query = request.GET.get('cliente')
    fecha_query = request.GET.get('fecha')
    
    if cliente_query:
        pedidos = pedidos.filter(
            Q(cliente__nombres__icontains=cliente_query) |
            Q(cliente__apellidos__icontains=cliente_query)
        )
    
    if fecha_query:
        pedidos = pedidos.filter(fecha__date=fecha_query)
        
    return render(request, "ordenes/lista.html", {
        "pedidos": pedidos
    })

@login_required
def ver_pedido_admin(request, id):
    orden = get_object_or_404(Orden, id=id)
    return render(request, "ordenes/detalle.html", {
        "orden": orden
    })

@login_required
def crear_entrega(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    conductores = Usuario.objects.filter(rol="conductor")
    vehiculos = Vehiculo.objects.all()

    if request.method == "POST":
        conductor_id = request.POST.get("conductor")
        vehiculo_id = request.POST.get("vehiculo")

        if conductor_id and vehiculo_id:
            Entrega.objects.create(
                pedido=orden,
                conductor_id=conductor_id,
                vehiculo_id=vehiculo_id
            )

            orden.estado = "en_ruta"
            orden.conductor_id = conductor_id
            orden.fecha_toma_entrega = timezone.now()
            orden.save()

            return redirect("ordenes:lista_pedidos_admin")
        else:
            return render(request, "ordenes/asignar_entrega.html", {
                "orden": orden,
                "conductores": conductores,
                "vehiculos": vehiculos,
                "error": "Por favor selecciona un conductor y un vehículo."
            })

    return render(request, "ordenes/asignar_entrega.html", {
        "orden": orden,
        "conductores": conductores,
        "vehiculos": vehiculos
    })

@login_required
def editar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        
        if nuevo_estado == "en_ruta" and orden.estado != "en_ruta":
            orden.fecha_toma_entrega = timezone.now()
        elif nuevo_estado == "entregado" and orden.estado != "entregado":
            orden.fecha_entrega_real = timezone.now()
            
        orden.estado = nuevo_estado
        orden.save()
        return redirect("ordenes:lista_pedidos_admin")
    return render(request, "ordenes/detalle.html", {"orden": orden})

@login_required
def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    orden.delete()
    return redirect("ordenes:lista_pedidos_admin")
