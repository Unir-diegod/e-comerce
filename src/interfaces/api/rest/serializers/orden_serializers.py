"""
Serializers para Orden - Validación de entrada/salida
"""
from rest_framework import serializers
from uuid import UUID
from application.dto.orden_dto import (
    CrearOrdenDTO,
    AgregarLineaOrdenDTO,
    LineaOrdenDTO,
    OrdenDTO
)


class CrearOrdenSerializer(serializers.Serializer):
    """
    Serializer para crear una orden.
    
    Solo valida formato, NO reglas de negocio.
    """
    cliente_id = serializers.UUIDField(required=True)
    
    def to_dto(self) -> CrearOrdenDTO:
        """Convierte datos validados a DTO de aplicación"""
        return CrearOrdenDTO(
            cliente_id=self.validated_data['cliente_id']
        )


class AgregarLineaOrdenSerializer(serializers.Serializer):
    """
    Serializer para agregar una línea a una orden.
    
    Solo valida formato, NO reglas de negocio.
    """
    producto_id = serializers.UUIDField(required=True)
    cantidad = serializers.IntegerField(required=True, min_value=1)
    
    def to_dto(self, orden_id: UUID) -> AgregarLineaOrdenDTO:
        """Convierte datos validados a DTO de aplicación"""
        validated = self.validated_data
        return AgregarLineaOrdenDTO(
            orden_id=orden_id,
            producto_id=validated['producto_id'],
            cantidad=validated['cantidad']
        )


class LineaOrdenSerializer(serializers.Serializer):
    """
    Serializer de salida para LineaOrden.
    
    Mapea desde LineaOrdenDTO.
    """
    producto_id = serializers.UUIDField()
    cantidad = serializers.IntegerField()
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrdenSerializer(serializers.Serializer):
    """
    Serializer de salida para Orden.
    
    Mapea desde OrdenDTO.
    """
    id = serializers.UUIDField(read_only=True)
    cliente_id = serializers.UUIDField()
    estado = serializers.CharField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad_items = serializers.IntegerField()
    lineas = LineaOrdenSerializer(many=True)
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
    
    @staticmethod
    def from_dto(dto: OrdenDTO) -> dict:
        """Convierte DTO a diccionario para serializar"""
        return {
            'id': dto.id,
            'cliente_id': dto.cliente_id,
            'estado': dto.estado,
            'total': dto.total,
            'cantidad_items': dto.cantidad_items,
            'lineas': [
                {
                    'producto_id': linea.producto_id,
                    'cantidad': linea.cantidad,
                    'precio_unitario': linea.precio_unitario,
                    'subtotal': linea.subtotal
                }
                for linea in dto.lineas
            ],
            'activo': dto.activo,
            'fecha_creacion': dto.fecha_creacion,
            'fecha_modificacion': dto.fecha_modificacion
        }
