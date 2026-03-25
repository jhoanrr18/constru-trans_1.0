from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from ordenes.models import Orden

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


from ordenes.models import Orden, DetalleOrden

from django.db.models import Sum
from django.utils.timezone import now


def registro(request):

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        email = request.POST.get("correo")
        telefono = request.POST.get("telefono")

        tipo_documento = request.POST.get("tipo_documento")
        documento = request.POST.get("documento")

        rol = request.POST.get("rol")

        password = request.POST.get("contrasena")
        confirmar = request.POST.get("confirmar_contrasena")

        if password != confirmar:
            return render(request, "usuarios/registro.html", {
                "error": "Las contraseñas no coinciden"
            })

        if User.objects.filter(username=email).exists():
            return render(request, "usuarios/registro.html", {
                "error": "Este correo ya está registrado"
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        Usuario.objects.create(
            user=user,
            nombre=nombre,
            telefono=telefono,
            rol=rol,
            tipo_documento=tipo_documento,
            documento=documento
        )

        return redirect("login")

    return render(request, "usuarios/registro.html")


def login_usuario(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            try:
                usuario = user.usuario
            except Usuario.DoesNotExist:
                return render(request, "usuarios/login.html", {
                    "error": "El usuario no tiene perfil completo. Contacta al administrador."
                })

            login(request, user)

            if usuario.rol == "admin":
                return redirect("panel")

            elif usuario.rol == "cliente":
                return redirect("panel_cliente")


            elif usuario.rol == "conductor":
                return redirect("panel_conductor")

            elif usuario.rol == "empleado":
                return redirect("panel")

        else:
            return render(request, "usuarios/login.html", {
                "error": "Usuario o contraseña incorrectos"
            })

    return render(request, "usuarios/login.html")


@login_required
def panel(request):

    try:
        usuario = request.user.usuario
    except Usuario.DoesNotExist:
        messages.error(request, "Tu usuario no tiene perfil completo. Por favor cierra sesión e inicia sesión con un usuario de la lista.")
        return redirect("login")

    if usuario.rol == "admin":

        pedidos_pendientes = Orden.objects.filter(estado="pendiente").count()
        conductores = Usuario.objects.filter(rol="conductor").count()
        entregas_hoy = Orden.objects.filter(
            estado="entregado",
            fecha__date=now().date()
        ).count()
        clientes = Usuario.objects.filter(rol="cliente").count()

        pedidos_recientes = Orden.objects.all().order_by("-fecha")[:5]

        context = {
            "pedidos_pendientes": pedidos_pendientes,
            "conductores": conductores,
            "entregas_hoy": entregas_hoy,
            "clientes": clientes,
            "pedidos_recientes": pedidos_recientes
        }

        return render(request, "dashboard/panel-admin.html", context)

    elif usuario.rol == "cliente":
        return redirect("panel_cliente")

    elif usuario.rol == "conductor":
        return redirect("panel_conductor")

    elif usuario.rol == "empleado":
        return render(request, "usuarios/panel-empleado.html")

    return redirect("login")


@login_required
def panel_conductor(request):

    conductor = request.user.usuario

    pedidos = Orden.objects.filter(conductor=conductor)

    return render(request, "usuarios/panel-conductor.html", {
        "pedidos": pedidos
    })


@login_required
def perfil_conductor(request):

    conductor = request.user.usuario

    vehiculo = None

    pedidos = Orden.objects.filter(conductor=conductor)

    context = {
        "conductor": conductor,
        "vehiculo": vehiculo,
        "pedidos": pedidos
    }

    return render(request, "usuarios/perfil-conductor.html", context)


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


def cerrar_sesion(request):

    logout(request)

    return redirect("login")


@login_required
def lista_usuarios(request):

    usuarios = Usuario.objects.all()

    return render(request, "dashboard/usuarios_lista.html", {
        "usuarios": usuarios
    })


@login_required
def eliminar_usuario(request, id):

    usuario = Usuario.objects.get(id=id)
    usuario.delete()

    return redirect("lista_usuarios")


@login_required
def editar_usuario(request, id):

    usuario = Usuario.objects.get(id=id)

    if request.method == "POST":

        usuario.nombre = request.POST.get("nombre")
        usuario.telefono = request.POST.get("telefono")
        usuario.rol = request.POST.get("rol")

        usuario.save()

        return redirect("lista_usuarios")

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
def lista_vehiculos(request):

    vehiculos = Vehiculo.objects.all()

    return render(request, "dashboard/vehiculos_lista.html", {
        "vehiculos": vehiculos
    })


@login_required
def reportes_admin(request):

    total_ordenes = Orden.objects.count()
    pendientes = Orden.objects.filter(estado="pendiente").count()
    en_ruta = Orden.objects.filter(estado="en_ruta").count()
    entregadas = Orden.objects.filter(estado="entregado").count()

    context = {
        "total": total_ordenes,
        "pendientes": pendientes,
        "en_ruta": en_ruta,
        "entregadas": entregadas,
    }

    return render(request, "dashboard/reportes.html", context)


@login_required
def panel_cliente(request):

    cliente = request.user.usuario

    pedidos = Orden.objects.filter(cliente=cliente)

    pedidos_activos = pedidos.filter(estado="pendiente").count()
    entregadas = pedidos.filter(estado="entregado").count()

    total_gastado = pedidos.aggregate(total=Sum("precio"))["total"] or 0

    ultimos_pedidos = pedidos.order_by("-fecha")[:5]

    context = {
        "pedidos_activos": pedidos_activos,
        "entregadas": entregadas,
        "total_gastado": total_gastado,
        "ultimos_pedidos": ultimos_pedidos
    }

    return render(request, "cliente/dashboard.html", context)


@login_required
def perfil_cliente(request):

    cliente = request.user.usuario

    return render(request, "cliente/perfil.html", {
        "cliente": cliente
    })


@login_required
def crear_pedido(request):

    try:
        cliente = request.user.usuario
    except Usuario.DoesNotExist:
        messages.error(request, "No se encontró el perfil de usuario. Por favor cierra sesión e inicia de nuevo.")
        return redirect("login")

    materiales = Material.objects.all()

    if request.method == "POST":

        material_id = request.POST.get("material")
        cantidad = request.POST.get("cantidad")
        direccion = request.POST.get("direccion")

        if not material_id or not cantidad or not direccion:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("crear_pedido")

        try:
            cantidad = int(cantidad)
        except ValueError:
            messages.error(request, "Cantidad inválida")
            return redirect("crear_pedido")

        if cantidad <= 0:
            messages.error(request, "Cantidad debe ser mayor a 0")
            return redirect("crear_pedido")

        material = get_object_or_404(Material, pk=material_id)

        if material.stock < cantidad:
            messages.error(request, "No hay stock suficiente del material seleccionado")
            return redirect("crear_pedido")

        total = material.precio * cantidad

        orden = Orden.objects.create(
            cliente=cliente,
            direccion_origen="Bodega",
            direccion_destino=direccion,
            precio=total,
            estado="pendiente"
        )

        DetalleOrden.objects.create(
            orden=orden,
            material=material,
            cantidad=cantidad
        )

        material.stock -= cantidad
        material.save()

        messages.success(request, "Pedido creado correctamente")
        return redirect("mis_pedidos")

    return render(request, "cliente/crear_pedido.html", {
        "materiales": materiales
    })


@login_required
def mis_pedidos(request):

    try:
        cliente = request.user.usuario
    except Usuario.DoesNotExist:
        messages.error(request, "No se encontró el perfil de usuario. Por favor cierra sesión e inicia de nuevo.")
        return redirect("login")

    try:
        pedidos = Orden.objects.filter(cliente=cliente).order_by("-fecha")
    except Exception:
        messages.error(request, "Error al cargar tus pedidos. Intenta nuevamente más tarde.")
        pedidos = Orden.objects.none()

    return render(request, "cliente/mis_pedidos.html", {
        "pedidos": pedidos
    })


@login_required
def seguimiento_pedidos(request):

    cliente = request.user.usuario

    pedidos = Orden.objects.filter(
        cliente=cliente
    ).order_by("-fecha")

    return render(request, "cliente/seguimiento.html", {
        "pedidos": pedidos
    })


@login_required
def historial_pedidos(request):

    cliente = request.user.usuario

    pedidos = Orden.objects.filter(
        cliente=cliente,
        estado="entregado"
    ).order_by("-fecha")

    return render(request, "cliente/historial.html", {
        "pedidos": pedidos
    })


@login_required
def lista_materiales(request):

    materiales = Material.objects.all()

    return render(request, "dashboard/materiales_lista.html", {
        "materiales": materiales
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
import json

@login_required
def crear_material(request):

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tipo = request.POST.get("tipo")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")

        if not nombre or not precio or not stock or not tipo:
            messages.error(request, "Campos obligatorios vacíos")
            return redirect("crear_material")

        if Material.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, "Ya existe un material con ese nombre")
            return redirect("crear_material")

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            messages.error(request, "Precio y stock deben ser numéricos")
            return redirect("crear_material")

        if precio <= 0:
            messages.error(request, "El precio debe ser mayor a 0")
            return redirect("crear_material")

        if stock < 0:
            messages.error(request, "El stock no puede ser negativo")
            return redirect("crear_material")

        material = Material(
            nombre=nombre,
            descripcion=descripcion,
            tipo=tipo,
            precio=precio,
            stock=stock
        )

        material.full_clean()
        material.save()

        messages.success(request, "Material creado correctamente")
        return redirect("lista_materiales")

    return render(request, "dashboard/material_crear.html")
    

@login_required
def editar_material(request, id):
    usuario = None
    try:
        usuario = request.user.usuario
    except Exception:
        pass

    if not (
        request.user.is_superuser
        or request.user.is_staff
        or (usuario and usuario.rol == "admin")
    ):
        messages.error(request, "No tienes permisos para realizar esta acción")
        return redirect("lista_materiales")

    material = get_object_or_404(Material, id=id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        tipo = request.POST.get("tipo")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")

        # Validar campos obligatorios
        if not nombre or not precio or not stock or not tipo:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("editar_material", id=id)

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            messages.error(request, "Precio y stock deben ser números válidos")
            return redirect("editar_material", id=id)

        if precio <= 0:
            messages.error(request, "El precio debe ser mayor a 0")
            return redirect("editar_material", id=id)

        if stock < 0:
            messages.error(request, "El stock no puede ser negativo")
            return redirect("editar_material", id=id)

        # Validar nombre duplicado
        if Material.objects.filter(nombre__iexact=nombre).exclude(id=id).exists():
            messages.error(request, "Ya existe un material con ese nombre")
            return redirect("editar_material", id=id)

        # Actualizar
        material.nombre = nombre
        material.descripcion = descripcion
        material.tipo = tipo
        material.precio = precio
        material.stock = stock

        material.save()

        messages.success(request, "Material actualizado correctamente")
        return redirect("lista_materiales")

    return render(request, "dashboard/material_editar.html", {
        "material": material
    })


@login_required
@require_http_methods(["PATCH"])
def api_actualizar_material(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "No autenticado"}, status=401)

    if not hasattr(request.user, "usuario"):
        return JsonResponse({"error": "Perfil de usuario no encontrado"}, status=403)

    usuario = request.user.usuario
    if not (request.user.is_superuser or request.user.is_staff or usuario.rol == "admin"):
        return JsonResponse({"error": "No tienes permisos para realizar esta acción"}, status=403)

    material = get_object_or_404(Material, id=id)

    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        data = request.POST.dict()

    if not data:
        return JsonResponse({"error": "Al menos un campo debe ser enviado"}, status=400)

    campos_permitidos = {"nombre", "descripcion", "tipo", "precio", "stock"}
    campos_invalidos = [field for field in data.keys() if field not in campos_permitidos]
    if campos_invalidos:
        return JsonResponse({"error": f"Campos no permitidos: {', '.join(campos_invalidos)}"}, status=400)

    if "nombre" in data:
        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            return JsonResponse({"error": "El nombre no puede estar vacío"}, status=400)
        if Material.objects.filter(nombre__iexact=nombre).exclude(id=id).exists():
            return JsonResponse({"error": "Ya existe un material con ese nombre"}, status=400)
        material.nombre = nombre

    if "descripcion" in data:
        material.descripcion = data.get("descripcion", "")

    if "tipo" in data:
        material.tipo = data.get("tipo", "")

    if "precio" in data:
        precio = data.get("precio")
        try:
            precio = float(precio)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Precio debe ser numérico"}, status=400)
        if precio <= 0:
            return JsonResponse({"error": "El precio debe ser mayor a 0"}, status=400)
        material.precio = precio

    if "stock" in data:
        stock = data.get("stock")
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Stock debe ser numérico"}, status=400)
        if stock < 0:
            return JsonResponse({"error": "El stock no puede ser negativo"}, status=400)
        material.stock = stock

    try:
        material.full_clean()
        material.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"success": True, "mensaje": "Material actualizado correctamente"}, status=200)


@login_required
def eliminar_material(request, id):

    material = get_object_or_404(Material, id=id)

    if request.method == "POST":
        material.delete()
        messages.success(request, "Material eliminado correctamente")
        return redirect("lista_materiales")

    # Si alguien entra por URL directa
    messages.error(request, "Acción no permitida")
    return redirect("lista_materiales")




@login_required
def ver_pedido_admin(request, id):

    pedido = Orden.objects.get(id=id)

    return render(request, "dashboard/pedido_detalle.html", {
        "pedido": pedido
    })
    
@login_required
def lista_pedidos_admin(request):

    pedidos = Orden.objects.all().order_by("-fecha")

    return render(request, "dashboard/pedidos_lista.html", {
        "pedidos": pedidos
    })
    
@login_required
def crear_vehiculo(request):

    if request.method == "POST":

        placa = request.POST.get("placa")
        tipo = request.POST.get("tipo")
        capacidad = request.POST.get("capacidad")

        Vehiculo.objects.create(
            placa=placa,
            tipo=tipo,
            capacidad=capacidad,
            estado="disponible"
        )

        return redirect("lista_vehiculos")

    return render(request, "dashboard/vehiculo_crear.html")