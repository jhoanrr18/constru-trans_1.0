from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventario, name='inventario'),
    path('eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('', views.inicio, name='inicio'),
]