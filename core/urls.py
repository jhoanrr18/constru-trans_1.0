from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventario/', include('inventario.urls')),
    path('', include('inicio.urls')),    
    path('usuarios/', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),
    path('ordenes/', include('ordenes.urls')),
]