from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import UUID

from infrastructure.persistence.repositories.producto_repository_impl import ProductoRepositoryImpl
from application.use_cases.producto_use_cases import (
    CrearProductoUseCase,
    ObtenerProductoUseCase,
    ListarProductosUseCase
)
from ..serializers.producto_serializer import (
    CrearProductoSerializer,
    ProductoSerializer
)
from interfaces.permissions import PermisosPorMetodo

class ProductoListCreateView(APIView):
    """
    Endpoint de Productos
    
    Permisos:
    - GET: Cualquier usuario autenticado
    - POST: OPERADOR o ADMIN
    """
    permission_classes = [PermisosPorMetodo]
    
    def get(self, request):
        repo = ProductoRepositoryImpl()
        use_case = ListarProductosUseCase(repo)
        
        resultado = use_case.ejecutar()
        
        serializer = ProductoSerializer(resultado, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CrearProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()

        repo = ProductoRepositoryImpl()
        use_case = CrearProductoUseCase(repo)
        
        resultado = use_case.ejecutar(dto)
        
        serializer = ProductoSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductoDetailView(APIView):
    """
    Endpoint de detalle de Producto
    
    Permisos:
    - GET: Cualquier usuario autenticado
    """
    permission_classes = [PermisosPorMetodo]
    
    def get(self, request, id: UUID):
        repo = ProductoRepositoryImpl()
        use_case = ObtenerProductoUseCase(repo)
        
        resultado = use_case.ejecutar(id)
        
        serializer = ProductoSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_200_OK)
