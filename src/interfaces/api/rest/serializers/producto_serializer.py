from decimal import Decimal
from rest_framework import serializers
from application.dto.producto_dto import CrearProductoDTO

class CrearProductoSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=50)
    nombre = serializers.CharField(max_length=200)
    descripcion = serializers.CharField()
    precio_monto = serializers.DecimalField(max_digits=20, decimal_places=2)
    precio_moneda = serializers.CharField(max_length=3)
    stock_actual = serializers.IntegerField(min_value=0)
    stock_minimo = serializers.IntegerField(min_value=0)

    def to_dto(self) -> CrearProductoDTO:
        return CrearProductoDTO(
            codigo=self.validated_data['codigo'],
            nombre=self.validated_data['nombre'],
            descripcion=self.validated_data['descripcion'],
            precio_monto=self.validated_data['precio_monto'],
            precio_moneda=self.validated_data['precio_moneda'],
            stock_actual=self.validated_data['stock_actual'],
            stock_minimo=self.validated_data['stock_minimo']
        )

class ProductoSerializer(serializers.Serializer):
    """Serializer de salida para Producto"""
    id = serializers.UUIDField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    precio = serializers.CharField() # String format
    precio_monto = serializers.DecimalField(max_digits=20, decimal_places=2)
    precio_moneda = serializers.CharField()
    stock_actual = serializers.IntegerField()
    stock_minimo = serializers.IntegerField()
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
