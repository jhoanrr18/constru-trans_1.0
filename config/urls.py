from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de recuperación de contraseña fuera del namespace para evitar NoReverseMatch
    path('usuarios/recuperar/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="usuarios/password_confirmar.html", success_url="/usuarios/recuperar/completo/"), 
         name='password_reset_confirm'),
    path('usuarios/recuperar/completo/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="usuarios/password_completo.html"), 
         name='password_reset_complete'),

    path('', include('apps.inicio.urls')),    
    path('usuarios/', include(('apps.usuarios.urls', 'usuarios'), namespace='usuarios')),
    path('clientes/', include(('apps.clientes.urls', 'clientes'), namespace='clientes')),
    path('inventario/', include(('apps.inventario.urls', 'inventario'), namespace='inventario')),
    path('compras/', include(('apps.compras.urls', 'compras'), namespace='compras')),
    path('transporte/', include(('apps.transporte.urls', 'transporte'), namespace='transporte')),
    path('ordenes/', include(('apps.ordenes.urls', 'ordenes'), namespace='ordenes')),
    path('facturacion/', include(('apps.facturacion.urls', 'facturacion'), namespace='facturacion')),
    path('reportes/', include(('apps.reportes.urls', 'reportes'), namespace='reportes')),
]