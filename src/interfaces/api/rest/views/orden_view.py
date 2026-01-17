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

class OrdenListCreateView(APIView):
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
    def post(self, request, id: UUID):
        repo_orden = OrdenRepositoryImpl()
        repo_producto = ProductoRepositoryImpl()
        
        use_case = ConfirmarOrdenConStockUseCase(repo_orden, repo_producto)
        
        resultado = use_case.ejecutar(id)
        
        serializer = OrdenSerializer(resultado)
        return Response(serializer.data, status=status.HTTP_200_OK)
