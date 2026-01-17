"""
Controller/View para Producto - Adaptador REST que llama a UseCases
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from uuid import UUID

from application.use_cases.producto_use_cases import (
    CrearProductoUseCase,
    ObtenerProductoUseCase,
    ListarProductosUseCase
)
from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl
from interfaces.api.rest.serializers.producto_serializers import (
    CrearProductoSerializer,
    ProductoSerializer
)


@api_view(['POST'])
def crear_producto(request):
    """
    POST /api/v1/productos
    
    Crea un nuevo producto.
    """
    # 1. Validar entrada
    serializer = CrearProductoSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # 2. Convertir a DTO
    dto = serializer.to_dto()
    
    # 3. Ejecutar caso de uso
    repo = ProductoRepositoryImpl()
    use_case = CrearProductoUseCase(repo)
    producto_dto = use_case.ejecutar(dto)
    
    # 4. Convertir DTO a respuesta
    response_data = ProductoSerializer.from_dto(producto_dto)
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def listar_productos(request):
    """
    GET /api/v1/productos
    
    Lista todos los productos disponibles.
    """
    # Ejecutar caso de uso
    repo = ProductoRepositoryImpl()
    use_case = ListarProductosUseCase(repo)
    productos_dto = use_case.ejecutar()
    
    # Convertir DTOs a respuesta
    response_data = [ProductoSerializer.from_dto(dto) for dto in productos_dto]
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def obtener_producto(request, producto_id):
    """
    GET /api/v1/productos/{id}
    
    Obtiene un producto por ID.
    """
    # Convertir string a UUID
    try:
        uuid_obj = UUID(producto_id)
    except ValueError:
        return Response(
            {'error': 'ID inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Ejecutar caso de uso
    repo = ProductoRepositoryImpl()
    use_case = ObtenerProductoUseCase(repo)
    producto_dto = use_case.ejecutar(uuid_obj)
    
    # Convertir DTO a respuesta
    response_data = ProductoSerializer.from_dto(producto_dto)
    
    return Response(response_data, status=status.HTTP_200_OK)
