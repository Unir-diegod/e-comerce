"""
Casos de uso relacionados con Cliente
"""
from typing import Optional
from uuid import UUID

from application.use_cases.base import CasoUsoBase
from application.dto.cliente_dto import CrearClienteDTO, ClienteDTO, ActualizarClienteDTO
from domain.repositories.cliente_repository import ClienteRepository
from domain.entities.cliente import Cliente
from domain.value_objects.email import Email
from domain.value_objects.telefono import Telefono
from domain.value_objects.documento_identidad import DocumentoIdentidad
from domain.exceptions.dominio import EntidadNoEncontrada


class CrearClienteUseCase(CasoUsoBase[CrearClienteDTO, ClienteDTO]):
    """
    Caso de uso: Crear un nuevo cliente.
    
    Punto de extensión: validaciones adicionales, notificaciones, eventos
    """
    
    def __init__(self, cliente_repository: ClienteRepository):
        self._cliente_repository = cliente_repository
    
    def ejecutar(self, request: CrearClienteDTO) -> ClienteDTO:
        """Crea un nuevo cliente"""
        
        # Validar duplicados
        email = Email(request.email)
        existente = self._cliente_repository.obtener_por_email(email)
        
        if existente:
            from domain.exceptions.dominio import ReglaNegocioViolada
            raise ReglaNegocioViolada(f"Ya existe un cliente con el email {request.email}")
        
        # Crear entidad
        cliente = Cliente(
            nombre=request.nombre,
            apellido=request.apellido,
            email=email,
            documento=DocumentoIdentidad(request.tipo_documento, request.numero_documento),
            telefono=Telefono(request.telefono) if request.telefono else None
        )
        
        # Persistir
        cliente_guardado = self._cliente_repository.guardar(cliente)
        
        # Punto de extensión: emitir evento ClienteCreado
        
        return ClienteDTO.desde_entidad(cliente_guardado)


class ObtenerClienteUseCase(CasoUsoBase[UUID, ClienteDTO]):
    """
    Caso de uso: Obtener un cliente por ID.
    """
    
    def __init__(self, cliente_repository: ClienteRepository):
        self._cliente_repository = cliente_repository
    
    def ejecutar(self, request: UUID) -> ClienteDTO:
        """Obtiene un cliente por ID"""
        cliente = self._cliente_repository.obtener_por_id(request)
        
        if not cliente:
            raise EntidadNoEncontrada(f"Cliente {request} no encontrado")
        
        return ClienteDTO.desde_entidad(cliente)


class ActualizarClienteUseCase(CasoUsoBase[ActualizarClienteDTO, ClienteDTO]):
    """
    Caso de uso: Actualizar datos de un cliente.
    """
    
    def __init__(self, cliente_repository: ClienteRepository):
        self._cliente_repository = cliente_repository
    
    def ejecutar(self, request: ActualizarClienteDTO) -> ClienteDTO:
        """Actualiza un cliente"""
        cliente = self._cliente_repository.obtener_por_id(request.id)
        
        if not cliente:
            raise EntidadNoEncontrada(f"Cliente {request.id} no encontrado")
        
        # Actualizar campos si se proporcionan
        if request.email:
            cliente.actualizar_email(Email(request.email))
        
        if request.telefono:
            cliente.actualizar_telefono(Telefono(request.telefono))
        
        # Persistir
        cliente_actualizado = self._cliente_repository.guardar(cliente)
        
        # Punto de extensión: emitir evento ClienteActualizado
        
        return ClienteDTO.desde_entidad(cliente_actualizado)
