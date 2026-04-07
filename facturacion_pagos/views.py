from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto

def inventario(request):
    query = request.GET.get('q')

    productos = Producto.objects.all()

    if query:
        productos = productos.filter(nombre__icontains=query)

    if request.method == 'POST':
        id_producto = request.POST.get('id')

        if id_producto:
            producto = Producto.objects.get(id=id_producto)
        else:
            producto = Producto()

        producto.nombre = request.POST['nombre']
        producto.cantidad = request.POST['cantidad']
        producto.precio = request.POST['precio']
        producto.save()

        return redirect('inventario')

    total = Producto.objects.count()
    stock_bajo = Producto.objects.filter(cantidad__lt=10).count()

    return render(request, 'inventario.html', {
        'productos': productos,
        'total': total,
        'stock_bajo': stock_bajo
    })


def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return redirect('inventario')