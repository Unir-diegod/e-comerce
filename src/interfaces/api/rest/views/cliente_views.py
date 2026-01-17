"""
Controller/View para Cliente - Adaptador REST que llama a UseCases
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from uuid import UUID

from application.use_cases.cliente_use_cases import (
    CrearClienteUseCase,
    ObtenerClienteUseCase
)
from infrastructure.persistence.repositories.cliente_repository_impl import ClienteRepositoryImpl
from interfaces.api.rest.serializers.cliente_serializers import (
    CrearClienteSerializer,
    ClienteSerializer
)


@api_view(['POST'])
def crear_cliente(request):
    """
    POST /api/v1/clientes
    
    Crea un nuevo cliente.
    
    Controller que:
    1. Valida entrada con serializer
    2. Convierte a DTO
    3. Llama al UseCase
    4. Convierte respuesta DTO a JSON
    
    NO contiene lógica de negocio.
    """
    # 1. Validar entrada
    serializer = CrearClienteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # 2. Convertir a DTO
    dto = serializer.to_dto()
    
    # 3. Ejecutar caso de uso
    repo = ClienteRepositoryImpl()
    use_case = CrearClienteUseCase(repo)
    cliente_dto = use_case.ejecutar(dto)
    
    # 4. Convertir DTO a respuesta
    response_data = ClienteSerializer.from_dto(cliente_dto)
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def obtener_cliente(request, cliente_id):
    """
    GET /api/v1/clientes/{id}
    
    Obtiene un cliente por ID.
    """
    # Convertir string a UUID
    try:
        uuid_obj = UUID(cliente_id)
    except ValueError:
        return Response(
            {'error': 'ID inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Ejecutar caso de uso
    repo = ClienteRepositoryImpl()
    use_case = ObtenerClienteUseCase(repo)
    cliente_dto = use_case.ejecutar(uuid_obj)
    
    # Convertir DTO a respuesta
    response_data = ClienteSerializer.from_dto(cliente_dto)
    
    return Response(response_data, status=status.HTTP_200_OK)
