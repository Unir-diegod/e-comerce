"""
Serializers para Producto - Validación de entrada/salida
"""
from rest_framework import serializers
from decimal import Decimal
from application.dto.producto_dto import CrearProductoDTO, ProductoDTO


class CrearProductoSerializer(serializers.Serializer):
    """
    Serializer para crear un producto.
    
    Solo valida formato, NO reglas de negocio.
    """
    codigo = serializers.CharField(
        max_length=50,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    nombre = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    descripcion = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
    precio_monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.01')
    )
    precio_moneda = serializers.CharField(
        max_length=3,
        required=True,
        default='USD'
    )
    stock_actual = serializers.IntegerField(
        required=True,
        min_value=0
    )
    stock_minimo = serializers.IntegerField(
        required=True,
        min_value=0,
        default=0
    )
    
    def to_dto(self) -> CrearProductoDTO:
        """Convierte datos validados a DTO de aplicación"""
        validated = self.validated_data
        return CrearProductoDTO(
            codigo=validated['codigo'],
            nombre=validated['nombre'],
            descripcion=validated['descripcion'],
            precio_monto=validated['precio_monto'],
            precio_moneda=validated['precio_moneda'],
            stock_actual=validated['stock_actual'],
            stock_minimo=validated['stock_minimo']
        )


class ProductoSerializer(serializers.Serializer):
    """
    Serializer de salida para Producto.
    
    Mapea desde ProductoDTO.
    """
    id = serializers.UUIDField(read_only=True)
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    descripcion = serializers.CharField()
    precio = serializers.CharField()  # Formateado
    precio_monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_moneda = serializers.CharField()
    stock_actual = serializers.IntegerField()
    stock_minimo = serializers.IntegerField()
    activo = serializers.BooleanField()
    fecha_creacion = serializers.DateTimeField()
    fecha_modificacion = serializers.DateTimeField()
    
    @staticmethod
    def from_dto(dto: ProductoDTO) -> dict:
        """Convierte DTO a diccionario para serializar"""
        return {
            'id': dto.id,
            'codigo': dto.codigo,
            'nombre': dto.nombre,
            'descripcion': dto.descripcion,
            'precio': dto.precio,
            'precio_monto': dto.precio_monto,
            'precio_moneda': dto.precio_moneda,
            'stock_actual': dto.stock_actual,
            'stock_minimo': dto.stock_minimo,
            'activo': dto.activo,
            'fecha_creacion': dto.fecha_creacion,
            'fecha_modificacion': dto.fecha_modificacion
        }
