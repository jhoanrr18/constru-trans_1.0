from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from apps.ordenes.models import Orden

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db.models import Sum, Q
from django.utils.timezone import now
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# ---------------- REGISTRO ----------------
def registro(request):
    if request.method == "POST":
        nombres = request.POST.get("nombres")
        apellidos = request.POST.get("apellidos")
        username = request.POST.get("usuario")
        email = request.POST.get("correo")
        telefono = request.POST.get("telefono")
        tipo_documento = request.POST.get("tipo_documento")
        documento = request.POST.get("documento")
        rol = "cliente" # Rol predeterminado (HU-01)
        password = request.POST.get("contrasena")
        confirmar = request.POST.get("confirmar_contrasena")

        if password != confirmar:
            return render(request, "usuarios/registro.html", {
                "error": "Las contraseñas no coinciden"
            })

        if User.objects.filter(username=username).exists():
            return render(request, "usuarios/registro.html", {
                "error": "Este nombre de usuario ya está registrado"
            })

        if User.objects.filter(email=email).exists():
            return render(request, "usuarios/registro.html", {
                "error": "Este correo ya está registrado"
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Usuario.objects.create(
            user=user,
            nombres=nombres,
            apellidos=apellidos,
            telefono=telefono,
            rol=rol,
            tipo_documento=tipo_documento,
            documento=documento
        )

        return redirect("usuarios:login")

    return render(request, "usuarios/registro.html")


from django.contrib.auth import views as auth_views

# ---------------- LOGIN ----------------
def login_usuario(request):
    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")

        # Intentar autenticar por username
        user = authenticate(request, username=identifier, password=password)

        # Si falla, intentar buscar por correo
        if user is None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            
            # Si es superusuario, creamos el perfil si no existe y entramos
            if user.is_superuser:
                Usuario.objects.get_or_create(
                    user=user,
                    defaults={'nombres': user.username, 'apellidos': '', 'rol': 'admin'}
                )
                return redirect(request.GET.get('next') or "usuarios:panel")

            # Para usuarios normales, verificamos el perfil usando filter() para evitar el error amarillo
            perfil = Usuario.objects.filter(user=user).first()
            if perfil:
                # Priorizar el parámetro 'next' para redirecciones post-login
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                if perfil.rol == "admin":
                    return redirect("usuarios:panel")
                elif perfil.rol == "cliente":
                    return redirect("usuarios:panel_cliente")
                elif perfil.rol == "conductor":
                    return redirect("usuarios:panel_conductor")
                else:
                    return redirect("usuarios:panel")
            else:
                logout(request)
                return render(request, "usuarios/login.html", {
                    "error": "Tu cuenta no tiene un perfil asignado."
                })
        else:
            return render(request, "usuarios/login.html", {
                "error": "Usuario o contraseña incorrectos"
            })

    return render(request, "usuarios/login.html")


# ---------------- PANEL ADMIN ----------------
@login_required
def panel(request):
    try:
        usuario = request.user.usuario
    except Usuario.DoesNotExist:
        if request.user.is_superuser:
            usuario = Usuario.objects.create(
                user=request.user,
                nombres=request.user.username,
                apellidos='',
                rol='admin',
                estado='activo'
            )
        else:
            logout(request)
            return redirect("usuarios:login")

    if usuario.rol == "admin":
        context = {
            "pedidos_pendientes": Orden.objects.filter(estado="pendiente").count(),
            "conductores": Usuario.objects.filter(rol="conductor").count(),
            "entregas_hoy": Orden.objects.filter(
                estado="entregado",
                fecha__date=now().date()
            ).count(),
            "clientes": Usuario.objects.filter(rol="cliente").count(),
            "pedidos_recientes": Orden.objects.all().order_by("-fecha")[:5]
        }
        return render(request, "dashboard/panel-admin.html", context)
    elif usuario.rol == "cliente":
        return panel_cliente(request)
    elif usuario.rol == "conductor":
        return panel_conductor(request)
    
    return redirect("usuarios:login")


# ---------------- CONDUCTOR ----------------
@login_required
def panel_conductor(request):
    try:
        conductor = request.user.usuario
    except Usuario.DoesNotExist:
        logout(request)
        return redirect("usuarios:login")
        
    pedidos_asignados = Orden.objects.filter(conductor=conductor).exclude(estado="entregado")
    entregas_completadas = Orden.objects.filter(conductor=conductor, estado="entregado")
    
    context = {
        "pedidos": pedidos_asignados,
        "entregas_totales": entregas_completadas.count(),
        "pedidos_pendientes": pedidos_asignados.count(),
        "ultima_entrega": entregas_completadas.order_by("-fecha").first()
    }
    return render(request, "usuarios/panel-conductor.html", context)


@login_required
def pedidos_conductor(request):
    conductor = request.user.usuario
    pedidos = Orden.objects.filter(
        conductor=conductor
    ).exclude(estado="entregado")
    return render(request, "usuarios/pedidos_conductor.html", {
        "pedidos": pedidos
    })


@login_required
def mis_entregas(request):
    conductor = request.user.usuario
    entregas = Orden.objects.filter(
        conductor=conductor,
        estado="entregado"
    ).order_by("-fecha")
    return render(request, "usuarios/mis-entregas.html", {
        "entregas": entregas
    })


# ---------------- CLIENTE ----------------
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
    return render(request, "clientes/dashboard.html", context)


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
def perfil_admin(request):
    try:
        usuario = request.user.usuario
    except Usuario.DoesNotExist:
        logout(request)
        return redirect("usuarios:login")
        
    context = {
        "usuario": usuario,
        "usuarios_count": Usuario.objects.count(),
        "materiales_count": Material.objects.count(),
        "ordenes_count": Orden.objects.count(),
        "total_ventas": Orden.objects.aggregate(total=Sum("precio"))["total"] or 0,
        "entregados_count": Orden.objects.filter(estado="entregado").count()
    }
    return render(request, "dashboard/perfil.html", context)


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
    
    return render(request, "clientes/perfil.html", context)


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


# ---------------- GESTIÓN DE USUARIOS ----------------
@login_required
def crear_usuario(request):
    # Solo el administrador puede crear usuarios desde el panel
    if request.user.usuario.rol != 'admin':
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect("usuarios:panel")

    if request.method == "POST":
        nombre_completo = request.POST.get("nombre")
        email = request.POST.get("email")
        password = request.POST.get("password")
        telefono = request.POST.get("telefono")
        rol = request.POST.get("rol")
        tipo_doc = request.POST.get("tipo_doc")
        documento = request.POST.get("documento")

        # Validaciones básicas
        if not all([nombre_completo, email, password, telefono, rol, tipo_doc, documento]):
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, "dashboard/usuario_form.html", {"form_data": request.POST})

        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return render(request, "dashboard/usuario_form.html", {"form_data": request.POST})

        # Dividir nombre completo en nombres y apellidos
        partes = nombre_completo.split(' ', 1)
        nombres = partes[0]
        apellidos = partes[1] if len(partes) > 1 else ''

        try:
            # Crear User de Django
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            # Crear Perfil Usuario
            Usuario.objects.create(
                user=user,
                nombres=nombres,
                apellidos=apellidos,
                telefono=telefono,
                rol=rol,
                tipo_documento=tipo_doc,
                documento=documento,
                estado='activo'
            )
            messages.success(request, f"Usuario {nombres} creado correctamente.")
            return redirect("usuarios:lista_usuarios")
        except Exception as e:
            messages.error(request, f"Error al crear usuario: {e}")
            return render(request, "dashboard/usuario_form.html", {
                "error": str(e),
                "form_data": request.POST
            })

    return render(request, "dashboard/usuario_form.html")

@login_required
def lista_usuarios(request):
    usuarios_list = Usuario.objects.all().order_by('-id')
    
    # Aplicar búsqueda si existe
    query = request.GET.get('q')
    if query:
        usuarios_list = usuarios_list.filter(
            Q(nombres__icontains=query) | 
            Q(user__email__icontains=query) |
            Q(documento__icontains=query)
        )
    
    # Separar por roles
    admins = usuarios_list.filter(rol='admin')
    clientes = usuarios_list.filter(rol='cliente')
    conductores = usuarios_list.filter(rol='conductor')
    
    context = {
        "admins": admins,
        "clientes": clientes,
        "conductores": conductores,
        "query": query
    }
        
    return render(request, "dashboard/usuarios_lista.html", context)


@login_required
def eliminar_usuario(request, id):
    # Solo el administrador puede eliminar usuarios
    if request.user.usuario.rol != 'admin':
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect("usuarios:panel")

    usuario_obj = get_object_or_404(Usuario, id=id) 
    usuario_obj.delete()
    messages.success(request, "Usuario eliminado correctamente.")
    return redirect("usuarios:lista_usuarios")


@login_required
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    
    # Solo el administrador puede editar otros usuarios
    if request.user.usuario.rol != 'admin' and request.user.usuario != usuario:
        messages.error(request, "No tienes permisos para editar este perfil.")
        return redirect("usuarios:panel")

    if request.method == "POST":
        usuario.nombres = request.POST.get("nombres")
        usuario.apellidos = request.POST.get("apellidos")
        usuario.telefono = request.POST.get("telefono")
        
        # Solo el administrador puede cambiar el rol (HU-05)
        if request.user.usuario.rol == "admin":
            usuario.rol = request.POST.get("rol")
            
        usuario.save()
        messages.success(request, "Cambios guardados exitosamente.")
        return redirect("usuarios:lista_usuarios")
    return render(request, "dashboard/editar_usuario.html", {
        "usuario": usuario
    })


@login_required
def lista_conductores(request):
    conductores = Usuario.objects.filter(rol="conductor")
    return render(request, "dashboard/conductores_lista.html", {
        "conductores": conductores
    })


@login_required
def perfil_conductor(request):
    conductor_id = request.GET.get('id')
    
    # Si se pasa un ID y el usuario es admin, buscamos a ese conductor
    if conductor_id and request.user.usuario.rol == 'admin':
        conductor = get_object_or_404(Usuario, id=conductor_id)
    else:
        # De lo contrario, usamos el perfil del usuario actual
        try:
            conductor = request.user.usuario
        except Usuario.DoesNotExist:
            logout(request)
            return redirect("usuarios:login")
        
    pedidos = Orden.objects.filter(conductor=conductor)
    
    # Intentar obtener el último vehículo asignado
    from apps.ordenes.models import Entrega
    ultima_entrega = Entrega.objects.filter(conductor=conductor).order_by('-fecha').first()
    vehiculo = ultima_entrega.vehiculo if ultima_entrega else None

    return render(request, "usuarios/perfil-conductor.html", {
        "conductor": conductor,
        "pedidos": pedidos,
        "vehiculo": vehiculo
    })


# ---------------- GESTIÓN DE VEHÍCULOS ----------------
@login_required
def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, "dashboard/vehiculos_lista.html", {
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
        return redirect("usuarios:lista_vehiculos")
    return render(request, "dashboard/vehiculo_crear.html")


# ---------------- GESTIÓN DE MATERIALES ----------------
@login_required
def materiales_lista(request):
    query = request.GET.get('q')
    if query:
        materiales = Material.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(tipo__icontains=query)
        )
    else:
        materiales = Material.objects.all()
    
    return render(request, "dashboard/materiales_lista.html", {
        "materiales": materiales
    })


@login_required
def api_materiales(request):
    materiales = Material.objects.all().values('id', 'nombre', 'precio', 'stock', 'tipo')
    return JsonResponse(list(materiales), safe=False)


@login_required
def crear_material(request):
    # Solo el administrador puede crear materiales
    if request.user.usuario.rol != 'admin':
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect("usuarios:panel")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        tipo = request.POST.get("tipo")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")

        if not all([nombre, tipo, precio, stock]):
            messages.error(request, "Los campos Nombre, Tipo, Precio y Stock son obligatorios.")
            return render(request, "dashboard/material_form.html", {"material": request.POST})

        try:
            Material.objects.create(
                nombre=nombre,
                tipo=tipo,
                descripcion=descripcion,
                precio=precio,
                stock=stock
            )
            messages.success(request, "Material creado correctamente.")
            return redirect("usuarios:materiales_lista")
        except Exception as e:
            messages.error(request, f"Error al crear material: {e}")
            return render(request, "dashboard/material_form.html", {
                "error": str(e),
                "material": request.POST
            })

    return render(request, "dashboard/material_form.html")


@login_required
def editar_material(request, id):
    material = get_object_or_404(Material, id=id)
    if request.method == "POST":
        material.nombre = request.POST.get("nombre")
        material.descripcion = request.POST.get("descripcion")
        material.tipo = request.POST.get("tipo")
        material.precio = request.POST.get("precio")
        material.stock = request.POST.get("stock")
        material.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            messages.success(request, "Material actualizado correctamente.")
            return JsonResponse({"status": "success"})
            
        messages.success(request, "Material actualizado")
        return redirect("usuarios:materiales_lista")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            "id": material.id,
            "nombre": material.nombre,
            "descripcion": material.descripcion,
            "tipo": material.tipo,
            "precio": str(material.precio),
            "stock": material.stock
        })
        
    return render(request, "dashboard/material_editar.html", {"material": material})


@login_required
def eliminar_material(request, id):
    material = get_object_or_404(Material, id=id)
    material.delete()
    messages.success(request, "Material eliminado correctamente")
    return redirect("usuarios:materiales_lista")


# ---------------- REPORTES ----------------
@login_required
def reportes_admin(request):
    # Estadísticas de Órdenes
    ordenes = Orden.objects.all()
    context = {
        # Resumen de Órdenes
        "total_ordenes": ordenes.count(),
        "pendientes": ordenes.filter(estado="pendiente").count(),
        "en_ruta": ordenes.filter(estado="en_ruta").count(),
        "entregadas": ordenes.filter(estado="entregado").count(),
        
        # Resumen de Usuarios
        "total_clientes": Usuario.objects.filter(rol="cliente").count(),
        "total_conductores": Usuario.objects.filter(rol="conductor").count(),
        
        # Resumen de Inventario y Vehículos
        "total_materiales": Material.objects.count(),
        "total_vehiculos": Vehiculo.objects.count(),
        
        # Financiero
        "total_ingresos": ordenes.aggregate(total=Sum("precio"))["total"] or 0,
    }
    return render(request, "dashboard/reportes.html", context)


# ---------------- PEDIDOS CLIENTE ----------------
@login_required
def crear_pedido(request):
    cliente = request.user.usuario
    materiales = Material.objects.all()

    if request.method == "POST":
        materiales_ids = request.POST.getlist('material_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        direccion = request.POST.get("direccion")
        fecha_entrega = request.POST.get("fecha_entrega")

        if not materiales_ids or not direccion:
            messages.error(request, "Por favor, agrega al menos un material y la dirección.")
            return render(request, "clientes/crear_pedido.html", {
                "materiales": materiales
            })

        try:
            from apps.ordenes.models import DetalleOrden
            from django.db import transaction

            total_general = 0

            with transaction.atomic():
                # 1. Crear la Orden principal
                nueva_orden = Orden.objects.create(
                    cliente=cliente,
                    direccion_origen="Bodega Central",
                    direccion_destino=direccion,
                    estado="pendiente",
                    fecha_entrega_programada=fecha_entrega if fecha_entrega else None
                )

                # 2. Procesar cada material
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

                    # Crear el detalle
                    DetalleOrden.objects.create(
                        orden=nueva_orden,
                        material=material,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario
                    )
                    
                    # Descontar stock
                    material.stock -= cantidad
                    material.save()

                # 3. Actualizar el total de la orden
                nueva_orden.precio = total_general
                nueva_orden.save()

            messages.success(request, f"Pedido #{nueva_orden.id} creado correctamente.")
            return redirect("usuarios:mis_pedidos")

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, "clientes/crear_pedido.html", {
                "materiales": materiales
            })
        except Exception as e:
            messages.error(request, f"Error interno: {e}")
            return render(request, "clientes/crear_pedido.html", {
                "materiales": materiales
            })

    return render(request, "clientes/crear_pedido.html", {
        "materiales": materiales
    })


# ---------------- GESTIÓN DE PEDIDOS ADMIN ----------------
@login_required
def lista_pedidos_admin(request):
    pedidos = Orden.objects.all().order_by("-fecha")
    
    # Aplicar filtros si existen
    cliente_query = request.GET.get('cliente')
    fecha_query = request.GET.get('fecha')
    
    if cliente_query:
        pedidos = pedidos.filter(
            Q(cliente__nombres__icontains=cliente_query) |
            Q(cliente__apellidos__icontains=cliente_query)
        )
    
    if fecha_query:
        pedidos = pedidos.filter(fecha__date=fecha_query)
        
    return render(request, "dashboard/pedidos_lista.html", {
        "pedidos": pedidos
    })


@login_required
def ver_pedido_admin(request, id):
    orden = get_object_or_404(Orden, id=id)
    return render(request, "dashboard/pedido_detalle.html", {
        "orden": orden
    })


@login_required
def eliminar_orden(request, id):
    orden = get_object_or_404(Orden, id=id)
    # No se elimina permanentemente, se marca como cancelado
    orden.estado = "cancelado"
    orden.save()
    messages.warning(request, f"Pedido #{orden.id} ha sido cancelado.")
    
    if request.user.usuario.rol == "admin":
        return redirect("usuarios:lista_pedidos_admin")
    return redirect("usuarios:mis_pedidos")


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
        if request.user.usuario.rol == "admin":
            return redirect("usuarios:lista_pedidos_admin")
        return redirect("usuarios:mis_pedidos")
        
    return render(request, "clientes/editar_pedido.html", {
        "orden": orden,
        "materiales": materiales
    })


# ---------------- PASSWORD RESET ----------------
class CustomPasswordResetView(auth_views.PasswordResetView):
    pass


@login_required
def pedido_detalle(request, id):
    orden = get_object_or_404(Orden, id=id)
    usuario = request.user.usuario

    if request.method == "POST":
        if usuario.rol == "admin":
            nuevo_estado = request.POST.get("estado")
            if nuevo_estado in ["pendiente", "en_ruta", "entregado", "cancelado"]:
                orden.estado = nuevo_estado
                if nuevo_estado == "entregado":
                    orden.fecha_entrega_real = now()
                elif nuevo_estado == "en_ruta":
                    orden.fecha_toma_entrega = now()
                orden.save()
                messages.success(request, f"Estado del pedido #{orden.id} actualizado a {orden.get_estado_display()}.")
        
        elif usuario.rol == "conductor" and orden.conductor == usuario:
            accion = request.POST.get("accion")
            if accion == "confirmar":
                orden.estado = "entregado"
                orden.fecha_entrega_real = now()
                orden.save()
                messages.success(request, f"Entrega del pedido #{orden.id} confirmada.")
            elif accion == "cancelar":
                # El conductor cancela su participación o reporta problema, lo marcamos como pendiente para reasignar?
                # Según el usuario "cancelar la entrega", supongo que es cancelar el pedido o la entrega específica.
                # Vamos a marcarlo como cancelado por ahora.
                orden.estado = "cancelado"
                orden.save()
                messages.warning(request, f"Entrega del pedido #{orden.id} cancelada.")
        
        return redirect("usuarios:pedido_detalle", id=orden.id)

    return render(request, "dashboard/pedido_detalle.html", {
        "orden": orden
    })


# ---------------- LOGOUT ----------------
def cerrar_sesion(request):
    logout(request)
    return redirect("usuarios:login")
