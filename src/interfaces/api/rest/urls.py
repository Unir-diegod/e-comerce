from django.urls import path
from .views.cliente_view import ClienteListCreateView, ClienteDetailView
from .views.producto_view import ProductoListCreateView, ProductoDetailView
from .views.orden_view import OrdenListCreateView, OrdenLineaView, OrdenConfirmarView

urlpatterns = [
    # Clientes
    path('clientes', ClienteListCreateView.as_view(), name='cliente-list-create'),
    path('clientes/<uuid:id>', ClienteDetailView.as_view(), name='cliente-detail'),
    
    # Productos
    path('productos', ProductoListCreateView.as_view(), name='producto-list-create'),
    path('productos/<uuid:id>', ProductoDetailView.as_view(), name='producto-detail'),
    
    # Ordenes
    path('ordenes', OrdenListCreateView.as_view(), name='orden-create'),
    path('ordenes/<uuid:id>/confirmar', OrdenConfirmarView.as_view(), name='orden-confirmar'),
    
    # Extra: Agregar líneas (necesario para flujo completo)
    path('ordenes/<uuid:id>/lineas', OrdenLineaView.as_view(), name='orden-linea-add'),
]
