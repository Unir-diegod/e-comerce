"""
DTOs relacionados con Orden
"""
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from domain.entities.orden import Orden


@dataclass
class CrearOrdenDTO:
    """DTO para crear una orden"""
    cliente_id: UUID


@dataclass
class AgregarLineaOrdenDTO:
    """DTO para agregar una línea a una orden"""
    orden_id: UUID
    producto_id: UUID
    cantidad: int


@dataclass
class LineaOrdenDTO:
    """DTO de salida para línea de orden"""
    producto_id: UUID
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


@dataclass
class OrdenDTO:
    """DTO de salida para Orden"""
    id: UUID
    cliente_id: UUID
    estado: str
    total: Decimal
    cantidad_items: int
    lineas: List[LineaOrdenDTO]
    activo: bool
    fecha_creacion: datetime
    fecha_modificacion: datetime
    
    @classmethod
    def desde_entidad(cls, orden: Orden) -> 'OrdenDTO':
        """Crea un DTO desde una entidad Orden"""
        lineas_dto = [
            LineaOrdenDTO(
                producto_id=linea.producto_id,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario.monto,
                subtotal=linea.subtotal.monto
            )
            for linea in orden.lineas
        ]
        
        return cls(
            id=orden.id,
            cliente_id=orden.cliente_id,
            estado=orden.estado.value,
            total=orden.total.monto,
            cantidad_items=orden.cantidad_items,
            lineas=lineas_dto,
            activo=orden.activo,
            fecha_creacion=orden.fecha_creacion,
            fecha_modificacion=orden.fecha_modificacion
        )
