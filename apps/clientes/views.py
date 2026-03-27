from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Sum
from django.contrib import messages
from apps.ordenes.models import Orden
from apps.usuarios.models import Material, Usuario

@login_required
def panel_cliente(request):
    try:
        cliente = request.user.usuario
    except Usuario.DoesNotExist:
        logout(request)
        return redirect("usuarios:login")
        
    pedidos = Orden.objects.filter(cliente=cliente)
    context = {
        "pedidos_activos": pedidos.filter(estado="pendiente").count(),
        "entregadas": pedidos.filter(estado="entregado").count(),
        "total_gastado": pedidos.aggregate(total=Sum("precio"))["total"] or 0,
        "ultimos_pedidos": pedidos.order_by("-fecha")[:5]
    }
    return render(request, "clientes/lista.html", context)

@login_required
def mis_pedidos(request):
    cliente = request.user.usuario
    pedidos = Orden.objects.filter(
        cliente=cliente
    ).order_by("-fecha")
    return render(request, "clientes/mis_pedidos.html", {
        "pedidos": pedidos
    })

@login_required
def perfil_cliente(request):
    try:
        cliente = request.user.usuario
    except Usuario.DoesNotExist:
        logout(request)
        return redirect("usuarios:login")
        
    pedidos = Orden.objects.filter(cliente=cliente)
    
    context = {
        "cliente": cliente,
        "total_pedidos": pedidos.count(),
        "pedidos_pendientes": pedidos.filter(estado="pendiente").count(),
        "en_ruta": pedidos.filter(estado="en_ruta").count(),
        "total_invertido": pedidos.aggregate(total=Sum("precio"))["total"] or 0
    }
    
    return render(request, "clientes/detalle.html", context)

@login_required
def seguimiento_pedidos(request):
    cliente = request.user.usuario
    pedidos = Orden.objects.filter(cliente=cliente).order_by("-fecha")
    return render(request, "clientes/seguimiento.html", {
        "pedidos": pedidos
    })

@login_required
def historial_pedidos(request):
    cliente = request.user.usuario
    pedidos = Orden.objects.filter(
        cliente=cliente, 
        estado="entregado"
    ).order_by("-fecha")
    return render(request, "clientes/historial.html", {
        "pedidos": pedidos
    })

@login_required
def crear_pedido(request):
    # Restricción: Solo clientes pueden solicitar pedidos
    if request.user.usuario.rol != 'cliente':
        messages.error(request, "Solo los clientes pueden solicitar nuevos pedidos.")
        return redirect("usuarios:panel")
        
    cliente = request.user.usuario
    materiales = Material.objects.all()

    if request.method == "POST":
        materiales_ids = request.POST.getlist('material_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        direccion = request.POST.get("direccion")
        fecha_entrega = request.POST.get("fecha_entrega")

        if not materiales_ids or not direccion:
            messages.error(request, "Por favor, agrega al menos un material y la dirección.")
            return render(request, "clientes/form.html", {
                "materiales": materiales,
                "action": "crear"
            })

        try:
            from apps.ordenes.models import DetalleOrden
            from django.db import transaction

            total_general = 0

            with transaction.atomic():
                nueva_orden = Orden.objects.create(
                    cliente=cliente,
                    direccion_origen="Bodega Central",
                    direccion_destino=direccion,
                    estado="pendiente",
                    fecha_entrega_programada=fecha_entrega if fecha_entrega else None
                )

                for m_id, cant in zip(materiales_ids, cantidades):
                    material = get_object_or_404(Material, id=m_id)
                    cantidad = int(cant)

                    if cantidad <= 0:
                        raise ValueError(f"La cantidad para {material.nombre} debe ser mayor a 0.")

                    if material.stock < cantidad:
                        raise ValueError(f"Stock insuficiente para {material.nombre}. Quedan {material.stock}.")

                    precio_unitario = material.precio
                    total_item = precio_unitario * cantidad
                    total_general += total_item

                    DetalleOrden.objects.create(
                        orden=nueva_orden,
                        material=material,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    
                    material.stock -= cantidad
                    material.save()

                nueva_orden.precio = total_general
                nueva_orden.save()

            messages.success(request, f"Pedido #{nueva_orden.id} creado correctamente.")
            return redirect("clientes:mis_pedidos")

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "clientes/form.html", {
                "materiales": materiales,
                "action": "crear"
            })
        except Exception as e:
            messages.error(request, f"Error interno: {e}")
            return render(request, "clientes/form.html", {
                "materiales": materiales,
                "action": "crear"
            })

    return render(request, "clientes/form.html", {
        "materiales": materiales,
        "action": "crear"
    })

@login_required
def editar_pedido(request, id):
    orden = get_object_or_404(Orden, id=id)
    materiales = Material.objects.all()
    
    if request.method == "POST":
        material_id = request.POST.get("material")
        cantidad = int(request.POST.get("cantidad"))
        direccion = request.POST.get("direccion")
        
        material = get_object_or_404(Material, id=material_id)
        
        orden.material = material
        orden.cantidad = cantidad
        orden.direccion_destino = direccion
        orden.precio = material.precio * cantidad
        orden.save()
        
        messages.success(request, f"Pedido #{orden.id} actualizado correctamente.")
        return redirect("clientes:mis_pedidos")
        
    return render(request, "clientes/form.html", {
        "orden": orden,
        "materiales": materiales,
        "action": "editar"
    })

@login_required
def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    orden.estado = "cancelado"
    orden.save()
    messages.warning(request, f"Pedido #{orden.id} ha sido cancelado.")
    return redirect("clientes:mis_pedidos")
