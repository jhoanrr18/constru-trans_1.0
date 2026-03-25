from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Orden, Entrega
from usuarios.models import Usuario, Vehiculo, Material

# 📋 LISTAR ÓRDENES
@login_required
def lista_ordenes(request):
    ordenes = Orden.objects.all().order_by("-fecha")
    return render(request, "ordenes/lista_ordenes.html", {
        "ordenes": ordenes
    })

@login_required
def crear_orden(request):
    cliente = request.user.usuario
    materiales = Material.objects.all()

    if request.method == "POST":
        material_id = request.POST.get("material")
        cantidad_str = request.POST.get("cantidad")
        direccion = request.POST.get("direccion")

        if not material_id or not cantidad_str or not direccion:
            return render(request, "cliente/crear_pedido.html", {
                "materiales": materiales,
                "error": "Por favor, completa todos los campos."
            })

        try:
            material = get_object_or_404(Material, id=material_id)
            cantidad = int(cantidad_str)
            total = material.precio * cantidad

            nueva_orden = Orden.objects.create(
                cliente=cliente,
                material=material,
                cantidad=cantidad,
                direccion_origen="Bodega Central",
                direccion_destino=direccion,
                precio=total,
                estado="pendiente"
            )
            
            return redirect("usuarios:mis_pedidos")

        except Exception as e:
            return render(request, "cliente/crear_pedido.html", {
                "materiales": materiales,
                "error": f"Error interno: {e}"
            })

    return render(request, "cliente/crear_pedido.html", {
        "materiales": materiales
    })

# 🚚 CREAR ENTREGA AUTOMÁTICA
@login_required
def crear_entrega(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    conductores = Usuario.objects.filter(rol="conductor")
    vehiculos = Vehiculo.objects.all()

    if request.method == "POST":
        conductor_id = request.POST.get("conductor")
        vehiculo_id = request.POST.get("vehiculo")

        Entrega.objects.create(
            pedido=orden,
            conductor_id=conductor_id,
            vehiculo_id=vehiculo_id
        )

        orden.estado = "en_ruta"
        orden.conductor_id = conductor_id
        orden.save()

        return redirect("ordenes:lista_ordenes")

    return render(request, "ordenes/asignar_entrega.html", {
        "orden": orden,
        "conductores": conductores,
        "vehiculos": vehiculos
    })

@login_required
def editar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    if request.method == "POST":
        orden.estado = request.POST.get("estado")
        orden.save()
        return redirect("ordenes:lista_ordenes")
    return render(request, "dashboard/pedido_detalle.html", {"pedido": orden})

@login_required
def eliminar_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id)
    orden.delete()
    return redirect("ordenes:lista_ordenes")
