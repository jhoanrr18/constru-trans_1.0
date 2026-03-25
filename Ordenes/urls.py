from django.urls import path
from . import views

urlpatterns = [

    path("lista/", views.lista_ordenes, name="lista_ordenes"),
    path("crear/", views.crear_orden, name="crear_orden"),

    # Nuevas acciones CRUD para órdenes
    path("ver/<int:id>/", views.ver_orden, name="ver_orden"),
    path("editar/<int:id>/", views.editar_orden, name="editar_orden"),
    path("asignar-conductor/<int:id>/", views.asignar_conductor, name="asignar_conductor"),
    path("eliminar/<int:id>/", views.eliminar_orden, name="eliminar_orden"),

]