from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from apps.ordenes.models import Orden
from apps.usuarios.models import Usuario, Material, Vehiculo

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
    return render(request, "reportes/lista.html", context)
