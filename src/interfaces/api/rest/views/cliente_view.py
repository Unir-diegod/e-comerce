from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from uuid import UUID

from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from application.use_cases.cliente_use_cases import (
    CrearClienteUseCase,
    ObtenerClienteUseCase
)
from ..serializers.cliente_serializer import (
    CrearClienteSerializer,
    ClienteSerializer
)

class ClienteListCreateView(APIView):
    def post(self, request):
        serializer = CrearClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dto = serializer.to_dto()

        repo = ClienteRepositoryImpl()
        use_case = CrearClienteUseCase(repo)
        
        resultado = use_case.ejecutar(dto)
        
        # Output serialization
        output_serializer = ClienteSerializer(resultado)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class ClienteDetailView(APIView):
    def get(self, request, id: UUID):
        repo = ClienteRepositoryImpl()
        use_case = ObtenerClienteUseCase(repo)
        
        resultado = use_case.ejecutar(id)
        
        output_serializer = ClienteSerializer(resultado)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
