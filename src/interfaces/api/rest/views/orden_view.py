from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import UUID

from infrastructure.persistence.repositories.orden_repository_impl import OrdenRepositoryImpl
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl

from application.use_cases.orden_use_cases import (
    CrearOrdenUseCase,
    AgregarLineaOrdenUseCase,
    ConfirmarOrdenConStockUseCase
)
from ..serializers.orden_serializer import (
    CrearOrdenSerializer,
    AgregarLineaOrdenSerializer,
    OrdenSerializer
)
from interfaces.permissions import EsOperadorOAdmin
from interfaces.api.rest.throttling import (
    OrdenCreacionRateThrottle,
    OrdenConfirmacionRateThrottle
)


class OrdenListCreateView(APIView):
    """
    Endpoint de Órdenes
    
    Permisos:
    - POST: OPERADOR o ADMIN (operación crítica de negocio)
    
    Protección Anti-Abuso:
    - Rate limit: 20 órdenes/minuto por usuario
    """
    permission_classes = [EsOperadorOAdmin]
    throttle_classes = [OrdenCreacionRateThrottle]
    
    def post(self, request):
        serializer = CrearOrdenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()

        repo_orden = OrdenRepositoryImpl()
        repo_cliente = ClienteRepositoryImpl()
        
        use_case = CrearOrdenUseCase(repo_orden, repo_cliente)
        
        resultado = use_case.ejecutar(dto)
        
        serializer = OrdenSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrdenLineaView(APIView):
    """
    Endpoint para agregar líneas a una orden
    
    Permisos:
    - POST: OPERADOR o ADMIN
    
    Protección Anti-Abuso:
    - Rate limit: 20 operaciones/minuto por usuario
    """
    permission_classes = [EsOperadorOAdmin]
    throttle_classes = [OrdenCreacionRateThrottle]
    
    def post(self, request, id: UUID):
        serializer = AgregarLineaOrdenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto(orden_id=id)
        
        repo_orden = OrdenRepositoryImpl()
        repo_producto = ProductoRepositoryImpl()
        
        use_case = AgregarLineaOrdenUseCase(repo_orden, repo_producto)
        
        resultado = use_case.ejecutar(dto)
        
        serializer = OrdenSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrdenConfirmarView(APIView):
    """
    Endpoint para confirmar una orden (operación crítica)
    
    Permisos:
    - POST: OPERADOR o ADMIN
    
    Protección Anti-Abuso:
    - Rate limit: 10 confirmaciones/minuto por usuario
    - Operación sensible que afecta inventario y genera transacciones
    """
    permission_classes = [EsOperadorOAdmin]
    throttle_classes = [OrdenConfirmacionRateThrottle]
    
    def post(self, request, id: UUID):
        repo_orden = OrdenRepositoryImpl()
        repo_producto = ProductoRepositoryImpl()
        
        use_case = ConfirmarOrdenConStockUseCase(repo_orden, repo_producto)
        
        resultado = use_case.ejecutar(id)
        
        serializer = OrdenSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_200_OK)
