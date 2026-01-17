from rest_framework import serializers
from application.dto.orden_dto import CrearOrdenDTO, AgregarLineaOrdenDTO

class CrearOrdenSerializer(serializers.Serializer):
    cliente_id = serializers.UUIDField()

    def to_dto(self) -> CrearOrdenDTO:
        return CrearOrdenDTO(
            cliente_id=self.validated_data['cliente_id']
        )

class AgregarLineaOrdenSerializer(serializers.Serializer):
    producto_id = serializers.UUIDField()
    cantidad = serializers.IntegerField(min_value=1)

    def to_dto(self, orden_id) -> AgregarLineaOrdenDTO:
        return AgregarLineaOrdenDTO(
            orden_id=orden_id,
            producto_id=self.validated_data['producto_id'],
            cantidad=self.validated_data['cantidad']
        )

class LineaOrdenSerializer(serializers.Serializer):
    producto_id = serializers.UUIDField()
    cantidad = serializers.IntegerField()
    precio_unitario = serializers.DecimalField(max_digits=20, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=20, decimal_places=2)

class OrdenSerializer(serializers.Serializer):
    """Serializer de salida para Orden"""
    id = serializers.UUIDField()
    cliente_id = serializers.UUIDField()
    estado = serializers.CharField()
    total = serializers.DecimalField(max_digits=20, decimal_places=2)
    cantidad_items = serializers.IntegerField()
    lineas = LineaOrdenSerializer(many=True)
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
