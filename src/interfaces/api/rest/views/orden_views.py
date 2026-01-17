"""
Controller/View para Orden - Adaptador REST que llama a UseCases
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from uuid import UUID

from application.use_cases.orden_use_cases import (
    CrearOrdenUseCase,
    AgregarLineaOrdenUseCase,
    ConfirmarOrdenConStockUseCase
)
from infrastructure.persistence.repositories.orden_repository_impl import OrdenRepositoryImpl
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl
from interfaces.api.rest.serializers.orden_serializers import (
    CrearOrdenSerializer,
    AgregarLineaOrdenSerializer,
    OrdenSerializer
)


@api_view(['POST'])
def crear_orden(request):
    """
    POST /api/v1/ordenes
    
    Crea una nueva orden vacía para un cliente.
    """
    # 1. Validar entrada
    serializer = CrearOrdenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # 2. Convertir a DTO
    dto = serializer.to_dto()
    
    # 3. Ejecutar caso de uso
    orden_repo = OrdenRepositoryImpl()
    cliente_repo = ClienteRepositoryImpl()
    use_case = CrearOrdenUseCase(orden_repo, cliente_repo)
    orden_dto = use_case.ejecutar(dto)
    
    # 4. Convertir DTO a respuesta
    response_data = OrdenSerializer.from_dto(orden_dto)
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def agregar_linea_orden(request, orden_id):
    """
    POST /api/v1/ordenes/{id}/lineas
    
    Agrega un producto a la orden.
    """
    # Convertir string a UUID
    try:
        uuid_obj = UUID(orden_id)
    except ValueError:
        return Response(
            {'error': 'ID de orden inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 1. Validar entrada
    serializer = AgregarLineaOrdenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # 2. Convertir a DTO
    dto = serializer.to_dto(uuid_obj)
    
    # 3. Ejecutar caso de uso
    orden_repo = OrdenRepositoryImpl()
    producto_repo = ProductoRepositoryImpl()
    use_case = AgregarLineaOrdenUseCase(orden_repo, producto_repo)
    orden_dto = use_case.ejecutar(dto)
    
    # 4. Convertir DTO a respuesta
    response_data = OrdenSerializer.from_dto(orden_dto)
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def confirmar_orden(request, orden_id):
    """
    POST /api/v1/ordenes/{id}/confirmar
    
    Confirma la orden y descuenta stock atómicamente.
    
    CRÍTICO: Usa ConfirmarOrdenConStockUseCase que implementa
    control de concurrencia con SELECT FOR UPDATE.
    """
    # Convertir string a UUID
    try:
        uuid_obj = UUID(orden_id)
    except ValueError:
        return Response(
            {'error': 'ID de orden inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Ejecutar caso de uso con control de concurrencia
    orden_repo = OrdenRepositoryImpl()
    producto_repo = ProductoRepositoryImpl()
    use_case = ConfirmarOrdenConStockUseCase(orden_repo, producto_repo)
    orden_dto = use_case.ejecutar(uuid_obj)
    
    # Convertir DTO a respuesta
    response_data = OrdenSerializer.from_dto(orden_dto)
    
    return Response(response_data, status=status.HTTP_200_OK)
