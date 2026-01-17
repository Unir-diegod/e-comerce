"""
DTOs relacionados con Cliente
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime

from domain.entities.cliente import Cliente
from shared.enums.tipos_documento import TipoDocumento


@dataclass
class CrearClienteDTO:
    """DTO para crear un cliente"""
    nombre: str
    apellido: str
    email: str
    tipo_documento: TipoDocumento
    numero_documento: str
    telefono: Optional[str] = None


@dataclass
class ActualizarClienteDTO:
    """DTO para actualizar un cliente"""
    id: UUID
    email: Optional[str] = None
    telefono: Optional[str] = None


@dataclass
class ClienteDTO:
    """DTO de salida para Cliente"""
    id: UUID
    nombre: str
    apellido: str
    email: str
    tipo_documento: str
    numero_documento: str
    telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    
    @classmethod
    def desde_entidad(cls, cliente: Cliente) -> 'ClienteDTO':
        """Crea un DTO desde una entidad Cliente"""
        return cls(
            id=cliente.id,
            nombre=cliente.nombre,
            apellido=cliente.apellido,
            email=cliente.email.valor,
            tipo_documento=cliente.documento.tipo.value,
            numero_documento=cliente.documento.numero,
            telefono=cliente.telefono.valor if cliente.telefono else None,
            activo=cliente.activo,
            fecha_creacion=cliente.fecha_creacion,
            fecha_modificacion=cliente.fecha_modificacion
        )
